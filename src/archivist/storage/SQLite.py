import sqlite3
import uuid
from enum import IntEnum

from archivist.config.settings import CONV_PATH
from archivist.core.message import MessageNode, AssistantMessage
from archivist.core.conversation import Conversation


class Source(IntEnum):
    CONVERSATION = 1
    SUMMARY = 2
    MEMORY = 3


class SQLDB:
    """SQLite storage for conversations.

    Layout: conversation -> message (tree via parent_id) -> content (ordered parts).
    assistant_message holds assistant-only metadata (1:1 with message).
    Messages are immutable; edits are stored as new sibling branches.
    """

    def __init__(self):
        self._connect()
        self._create_tables()

    def _connect(self):
        """Open the DB file and set per-connection pragmas.

        foreign_keys is per-connection and must be set on every connect.
        journal_mode=WAL persists in the file; busy_timeout makes concurrent
        writers wait (up to 5s) instead of failing immediately.
        """
        self.conn = sqlite3.connect(CONV_PATH / "conversations.db")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")

    def _create_tables(self):
        """Create the schema on a fresh DB, or verify the version on an existing one.

        Uses PRAGMA user_version as the schema version. There is no migration
        logic: a version mismatch raises, so bump SCHEMA_VERSION on any
        incompatible change and delete/migrate the old file.
        """
        SCHEMA_VERSION = 2  # bumped: integer conv_id replaced conv_uuid FK

        # Build the CHECK from the enum so Python and SQL can't drift apart
        source_values = ",".join(str(s.value) for s in Source)

        # One row per conversation. id is the internal key, uuid the external one.
        CONVERSATION = """CREATE TABLE IF NOT EXISTS conversation (
            id          INTEGER PRIMARY KEY,
            uuid        TEXT NOT NULL UNIQUE,
            title       TEXT,
            time_ns     INTEGER NOT NULL
        ) STRICT;"""

        # One row per message. parent_id forms the branch tree: siblings share
        # a parent, and root messages have parent_id NULL.
        MESSAGE = f"""CREATE TABLE IF NOT EXISTS message (
            id          INTEGER PRIMARY KEY,
            uuid        TEXT NOT NULL UNIQUE,
            conv_id     INTEGER NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
            parent_id   INTEGER REFERENCES message(id) ON DELETE CASCADE,
            source      INTEGER NOT NULL CHECK (source IN ({source_values})),
            role        TEXT NOT NULL CHECK (role IN ('system','user','assistant','tool')),
            name        TEXT,
            time_ns     INTEGER NOT NULL
        ) STRICT;"""

        # Ordered parts of a message: text, or a file path for imgs, videos, etc.
        CONTENT = """CREATE TABLE IF NOT EXISTS content (
            id          INTEGER PRIMARY KEY,
            message_id  INTEGER NOT NULL REFERENCES message(id) ON DELETE CASCADE,
            position    INTEGER NOT NULL DEFAULT 0,
            type        TEXT NOT NULL,
            text        TEXT,
            path        TEXT,
            UNIQUE (message_id, position),
            CHECK (text IS NOT NULL OR path IS NOT NULL)
        ) STRICT;"""

        # Assistant-only tracking data (1:1 with message). Insert together
        # with the message, inside the same transaction.
        ASSISTANT = """CREATE TABLE IF NOT EXISTS assistant_message (
            message_id    INTEGER PRIMARY KEY REFERENCES message(id) ON DELETE CASCADE,
            model         TEXT NOT NULL,
            finish_reason TEXT
        ) STRICT;"""

        # content(message_id) is already covered by UNIQUE(message_id, position)
        INDEXES = """CREATE INDEX IF NOT EXISTS idx_message_conv   ON message(conv_id);
        CREATE INDEX IF NOT EXISTS idx_message_parent ON message(parent_id);
        """

        # # Tool Dataclass
        # TOOL = """CREATE TABLE IF NOT EXISTS tool_message (
        #     message_id  INTEGER PRIMARY KEY REFERENCES message(id) ON DELETE CASCADE,
        #     success     INTEGER NOT NULL DEFAULT 0,
        #     retry       INTEGER NOT NULL DEFAULT 0
        # ) STRICT;"""

        SCHEMA = "\n".join([CONVERSATION, MESSAGE, CONTENT, ASSISTANT, INDEXES])

        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            with self.conn:
                self.conn.executescript(SCHEMA)
                self.conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        elif version != SCHEMA_VERSION:
            raise RuntimeError(f"DB schema v{version}, code expects v{SCHEMA_VERSION}")

    # ---------- id lookups ----------

    def _get_conv_id(self, conv_uuid: uuid.UUID) -> int:
        """Return the internal integer id for a conversation uuid.

        Raises ValueError if the conversation isn't in the DB.
        """
        row = self.conn.execute(
            "SELECT id FROM conversation WHERE uuid = ?", (str(conv_uuid),)
        ).fetchone()
        if row is None:
            raise ValueError(f"conversation {conv_uuid} not in DB")
        return row["id"]

    def _get_db_id(self, msg_uuid: uuid.UUID) -> int:
        """Return the internal integer id for a message uuid.

        Raises ValueError if the message isn't in the DB (e.g. a parent that
        was never inserted).
        """
        row = self.conn.execute(
            "SELECT id FROM message WHERE uuid = ?", (str(msg_uuid),)
        ).fetchone()
        if row is None:
            raise ValueError(f"message {msg_uuid} not in DB")
        return row["id"]

    def _ensure_conversation(self, conv: Conversation) -> int:
        """Insert the conversation row if it doesn't exist; return its internal id.

        Existing rows are left untouched (INSERT OR IGNORE), so a changed
        title is NOT updated here.
        """
        self.conn.execute(
            "INSERT OR IGNORE INTO conversation (uuid, title, time_ns) VALUES (?, ?, ?)",
            (str(conv.conv_uuid), conv.title, conv.time_ns),
        )
        return self._get_conv_id(conv.conv_uuid)

    # ---------- inserts ----------

    def _insert_message(self, node: MessageNode, conv_id: int, source: Source) -> int:
        """Insert one message plus its content (and assistant row if applicable).

        Does not open a transaction; callers must wrap it in `with self.conn`
        so the message, content, and assistant rows commit or fail together.
        The parent message must already be in the DB. Returns the message's
        internal id.
        """
        msg = node.message
        parent_db_id = None if node.parent_id is None else self._get_db_id(node.parent_id)

        cur = self.conn.execute(
            """INSERT INTO message (uuid, conv_id, parent_id, source, role, name, time_ns)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(msg.id), conv_id, parent_db_id, int(source),
             msg.role, msg.name or None, msg.time_ns),
        )
        msg_db_id = cur.lastrowid

        # Temporary until basic text is stable
        self.conn.execute(
            """INSERT INTO content (message_id, position, type, text)
            VALUES (?, ?, ?, ?)""",
            (msg_db_id, 0, "text", msg.content.text),
        )

        # NOTE: attribute names assumed, adjust to your AssistantMessage dataclass
        if isinstance(msg, AssistantMessage):
            self.conn.execute(
                """INSERT INTO assistant_message (message_id, model, finish_reason)
                VALUES (?, ?, ?)""",
                (msg_db_id, msg.model, msg.finish_reason or None),
            )
        return msg_db_id

    def insert_message_node(self, node: MessageNode, conv: Conversation):
        """Persist a single new message, creating the conversation row if needed.

        This is the per-message call (e.g. after Conversation.add_message).
        The parent node must already have been inserted. Runs in one transaction.
        """
        with self.conn:
            conv_id = self._ensure_conversation(conv)
            self._insert_message(node, conv_id, Source.CONVERSATION)

    def insert_conversation(self, conv: Conversation):
        """Persist an entire in-memory conversation in one transaction.

        Fails if the conversation already exists. Relies on uuid_index
        iterating in insertion order so parents are inserted before children.
        """
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO conversation (uuid, title, time_ns) VALUES (?, ?, ?)",
                (str(conv.conv_uuid), conv.title, conv.time_ns),
            )
            conv_id = cur.lastrowid
            for node in conv.uuid_index.values():
                self._insert_message(node, conv_id, Source.CONVERSATION)

    # ---------- reads ----------

    def get_conversation(self, conv_uuid: uuid.UUID) -> list[dict]:
        """Load every message in a conversation (all branches), oldest first.

        Each dict is a message row plus:
          - parent_uuid: uuid of the parent message (None for roots)
          - model, finish_reason: assistant metadata (None for non-assistant)
          - content: list of content rows ordered by position
        Uses three queries total (messages, then all content), not one per message.
        Raises ValueError if the conversation doesn't exist.
        """
        conv_id = self._get_conv_id(conv_uuid)

        messages = [
            dict(r) for r in self.conn.execute(
                """SELECT m.*, p.uuid AS parent_uuid,
                          a.model, a.finish_reason
                FROM message m
                LEFT JOIN message p ON p.id = m.parent_id
                LEFT JOIN assistant_message a ON a.message_id = m.id
                WHERE m.conv_id = ?
                ORDER BY m.id""",
                (conv_id,),
            )
        ]
        # Index by internal id so content rows can be attached in one pass
        by_id = {m["id"]: m for m in messages}
        for m in messages:
            m["content"] = []

        for c in self.conn.execute(
            """SELECT c.* FROM content c
            JOIN message m ON m.id = c.message_id
            WHERE m.conv_id = ?
            ORDER BY c.message_id, c.position""",
            (conv_id,),
        ):
            by_id[c["message_id"]]["content"].append(dict(c))

        return messages

    def __del__(self):
        """Close the connection when the object is garbage collected."""
        self.conn.close()