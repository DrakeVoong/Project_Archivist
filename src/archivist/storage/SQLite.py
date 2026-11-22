import sqlite3
import uuid
from enum import IntEnum

from archivist.config.settings import CONV_PATH
from archivist.core.message import MessageNode, AssistantMessage
from archivist.core.conversation import Conversation

# Ai once again :c

class Source(IntEnum):
    CONVERSATION = 1
    SUMMARY = 2
    MEMORY = 3


class SQLDB:
    """SQLite storage for conversations.

    Layout: conversation -> message (tree via parent_uuid) -> content (ordered parts).
    assistant_message holds assistant-only metadata (1:1 with message).
    Messages are immutable; edits are stored as new sibling branches.

    Every table is keyed by the same uuid the in-memory objects use, so there
    is no uuid <-> integer translation layer. Rows are returned in insertion
    order via the implicit rowid (tie-break after time_ns).
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
        SCHEMA_VERSION = 3  # bumped: uuid TEXT primary keys replaced integer ids

        # Build the CHECK from the enum so Python and SQL can't drift apart
        source_values = ",".join(str(s.value) for s in Source)

        # One row per conversation, keyed by its uuid.
        # NOT NULL is explicit: SQLite allows NULL in non-integer primary keys.
        CONVERSATION = """CREATE TABLE IF NOT EXISTS conversation (
            uuid        TEXT NOT NULL PRIMARY KEY,
            title       TEXT,
            time_ns     INTEGER NOT NULL
        ) STRICT;"""

        # One row per message. parent_uuid forms the branch tree: siblings share
        # a parent, and root messages have parent_uuid NULL.
        MESSAGE = f"""CREATE TABLE IF NOT EXISTS message (
            uuid        TEXT NOT NULL PRIMARY KEY,
            conv_uuid   TEXT NOT NULL REFERENCES conversation(uuid) ON DELETE CASCADE,
            parent_uuid TEXT REFERENCES message(uuid) ON DELETE CASCADE,
            source      INTEGER NOT NULL CHECK (source IN ({source_values})),
            role        TEXT NOT NULL CHECK (role IN ('system','user','assistant','tool')),
            name        TEXT,
            time_ns     INTEGER NOT NULL
        ) STRICT;"""

        # Ordered parts of a message: text, or a file path for imgs, videos, etc.
        CONTENT = """CREATE TABLE IF NOT EXISTS content (
            id           INTEGER PRIMARY KEY,
            message_uuid TEXT NOT NULL REFERENCES message(uuid) ON DELETE CASCADE,
            position     INTEGER NOT NULL DEFAULT 0,
            type         TEXT NOT NULL,
            text         TEXT,
            path         TEXT,
            UNIQUE (message_uuid, position),
            CHECK (text IS NOT NULL OR path IS NOT NULL)
        ) STRICT;"""

        # Assistant-only tracking data (1:1 with message). Insert together
        # with the message, inside the same transaction.
        ASSISTANT = """CREATE TABLE IF NOT EXISTS assistant_message (
            message_uuid  TEXT NOT NULL PRIMARY KEY REFERENCES message(uuid) ON DELETE CASCADE,
            model         TEXT NOT NULL,
            finish_reason TEXT
        ) STRICT;"""

        # content(message_uuid) is already covered by UNIQUE(message_uuid, position)
        INDEXES = """CREATE INDEX IF NOT EXISTS idx_message_conv   ON message(conv_uuid);
        CREATE INDEX IF NOT EXISTS idx_message_parent ON message(parent_uuid);
        """

        # # Tool Dataclass
        # TOOL = """CREATE TABLE IF NOT EXISTS tool_message (
        #     message_uuid TEXT NOT NULL PRIMARY KEY REFERENCES message(uuid) ON DELETE CASCADE,
        #     success      INTEGER NOT NULL DEFAULT 0,
        #     retry        INTEGER NOT NULL DEFAULT 0
        # ) STRICT;"""

        SCHEMA = "\n".join([CONVERSATION, MESSAGE, CONTENT, ASSISTANT, INDEXES])

        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            with self.conn:
                self.conn.executescript(SCHEMA)
                self.conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        elif version != SCHEMA_VERSION:
            raise RuntimeError(f"DB schema v{version}, code expects v{SCHEMA_VERSION}")

    # ---------- inserts ----------

    def _ensure_conversation(self, conv: Conversation):
        """Insert the conversation row if it doesn't exist.

        Existing rows are left untouched (INSERT OR IGNORE), so a changed
        title is NOT updated here.
        """
        self.conn.execute(
            "INSERT OR IGNORE INTO conversation (uuid, title, time_ns) VALUES (?, ?, ?)",
            (str(conv.conv_uuid), conv.title, conv.time_ns),
        )

    def _insert_message(self, node: MessageNode, conv_uuid: uuid.UUID, source: Source):
        """Insert one message plus its content (and assistant row if applicable).

        Does not open a transaction; callers must wrap it in `with self.conn`
        so the message, content, and assistant rows commit or fail together.
        The parent message must already be in the DB: the foreign key on
        parent_uuid raises sqlite3.IntegrityError otherwise.
        """
        msg = node.message
        msg_uuid = str(msg.id)
        parent_uuid = None if node.parent_id is None else str(node.parent_id)

        self.conn.execute(
            """INSERT INTO message (uuid, conv_uuid, parent_uuid, source, role, name, time_ns)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (msg_uuid, str(conv_uuid), parent_uuid, int(source),
             msg.role, msg.name or None, msg.time_ns),
        )

        # Temporary until basic text is stable
        self.conn.execute(
            """INSERT INTO content (message_uuid, position, type, text)
            VALUES (?, ?, ?, ?)""",
            (msg_uuid, 0, "text", msg.content.text),
        )

        if isinstance(msg, AssistantMessage):
            self.conn.execute(
                """INSERT INTO assistant_message (message_uuid, model, finish_reason)
                VALUES (?, ?, ?)""",
                (msg_uuid, msg.model, msg.finish_reason or None),
            )

    def insert_message_node(self, node: MessageNode, conv: Conversation):
        """Persist a single new message, creating the conversation row if needed.

        This is the per-message call (e.g. after Conversation.add_message).
        The parent node must already have been inserted. Runs in one transaction.
        """
        with self.conn:
            self._ensure_conversation(conv)
            self._insert_message(node, conv.conv_uuid, Source.CONVERSATION)

    def insert_conversation(self, conv: Conversation):
        """Persist an entire in-memory conversation in one transaction.

        Fails if the conversation already exists. Relies on uuid_index
        iterating in insertion order so parents are inserted before children.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO conversation (uuid, title, time_ns) VALUES (?, ?, ?)",
                (str(conv.conv_uuid), conv.title, conv.time_ns),
            )
            for node in conv.uuid_index.values():
                self._insert_message(node, conv.conv_uuid, Source.CONVERSATION)

    # ---------- reads ----------

    def get_conversation(self, conv_uuid: uuid.UUID) -> list[dict]:
        """Load every message in a conversation (all branches), oldest first.

        Each dict is a message row (uuid, conv_uuid, parent_uuid, source, role,
        name, time_ns) plus:
          - model, finish_reason: assistant metadata (None for non-assistant)
          - content: list of content rows ordered by position
        Uses three queries total (existence check, messages, then all content),
        not one per message.
        Raises ValueError if the conversation doesn't exist.
        """
        conv_key = str(conv_uuid)

        exists = self.conn.execute(
            "SELECT 1 FROM conversation WHERE uuid = ?", (conv_key,)
        ).fetchone()
        if exists is None:
            raise ValueError(f"conversation {conv_uuid} not in DB")

        messages = [
            dict(r) for r in self.conn.execute(
                """SELECT m.*, a.model, a.finish_reason
                FROM message m
                LEFT JOIN assistant_message a ON a.message_uuid = m.uuid
                WHERE m.conv_uuid = ?
                ORDER BY m.time_ns, m.rowid""",
                (conv_key,),
            )
        ]
        # Index by uuid so content rows can be attached in one pass
        by_uuid = {m["uuid"]: m for m in messages}
        for m in messages:
            m["content"] = []

        for c in self.conn.execute(
            """SELECT c.* FROM content c
            JOIN message m ON m.uuid = c.message_uuid
            WHERE m.conv_uuid = ?
            ORDER BY c.message_uuid, c.position""",
            (conv_key,),
        ):
            by_uuid[c["message_uuid"]]["content"].append(dict(c))

        return messages

    def __del__(self):
        """Close the connection when the object is garbage collected."""
        self.conn.close()