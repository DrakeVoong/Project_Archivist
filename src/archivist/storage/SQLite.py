import sqlite3
import uuid
from typing import List
from enum import IntEnum

from archivist.config.settings import CONV_PATH
from archivist.core.message import Message, MessageNode, UserMessage, AssistantMessage
from archivist.memory.conversation import Conversation

# Don't look at this AI mess for now

class Source(IntEnum):
    CONVERSATION = 1
    SUMMARY = 2
    MEMORY = 3

class SQLDB:
    def __init__(self):
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(CONV_PATH / "conversations.db")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def _create_tables(self):
        SCHEMA_VERSION = 1

        # Message Dataclass
        MESSAGE = """CREATE TABLE IF NOT EXISTS message (
            id              INTEGER PRIMARY KEY,
            uuid            TEXT NOT NULL UNIQUE,
            conv_uuid TEXT NOT NULL REFERENCES conversation(conv_uuid),
            parent_id INTEGER REFERENCES message(id),
            source          INTEGER NOT NULL,
            role            TEXT NOT NULL,
            name            TEXT NOT NULL,
            time_ns         INTEGER NOT NULL
        );"""

        # Conversation
        CONVERSATION = """CREATE TABLE IF NOT EXISTS conversation (
            conv_uuid       TEXT PRIMARY KEY NOT NULL,
            title           TEXT NOT NULL,
            creation_time   INTEGER NOT NULL
        );"""

        # Conv
        # Individual message in a conversation
        # CONV = """CREATE TABLE IF NOT EXISTS conv (
        #     message_id      INTEGER PRIMARY KEY REFERENCES message(id),
        #     conv_uuid       TEXT NOT NULL REFERENCES conversation(conv_uuid),
        #     parent_id       INTEGER REFERENCES conv(message_id)
        # );"""

        # Content 
        # Text and file location for imgs, videos, etc.
        CONTENT = """CREATE TABLE IF NOT EXISTS content (
            id              INTEGER PRIMARY KEY,
            message_id      INTEGER NOT NULL REFERENCES message(id),
            position    INTEGER NOT NULL DEFAULT 0,
            type            TEXT NOT NULL,
            text            TEXT,
            path            TEXT
        );"""

        # Assistant Dataclass
        ASSISTANT = """CREATE TABLE IF NOT EXISTS assistant_message (
            message_id      INTEGER PRIMARY KEY REFERENCES message(id),
            model           TEXT NOT NULL,
            finish_reason   TEXT NOT NULL DEFAULT ''
        );"""

        # Faster searches when inserting and retrieving message conversation
        INDEXES = """CREATE INDEX IF NOT EXISTS idx_message_conv   ON message(conv_uuid);
        CREATE INDEX IF NOT EXISTS idx_message_parent ON message(parent_id);
        CREATE INDEX IF NOT EXISTS idx_content_msg    ON content(message_id);
        """

        # # Tool Dataclass
        # TOOL = """CREATE TABLE IF NOT EXISTS tool_message (
        #     message_id      INTEGER PRIMARY KEY REFERENCES message(id),
        #     success         INTEGER NOT NULL DEFAULT 0,
        #     retry           INTEGER NOT NULL DEFAULT 0
        # );"""
        # 

        SCHEMA = "".join([MESSAGE, CONVERSATION, CONTENT, ASSISTANT, INDEXES])

        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            with self.conn:
                self.conn.executescript(SCHEMA)
                self.conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        elif version != SCHEMA_VERSION:
            raise RuntimeError(f"DB schema v{version}, code expects v{SCHEMA_VERSION}")

    def _get_db_id(self, msg_uuid: uuid.UUID) -> int:
        row = self.conn.execute(
            "SELECT id FROM message WHERE uuid = ?", (str(msg_uuid),)
        ).fetchone()
        if row is None:
            raise ValueError(f"message {msg_uuid} not in DB")
        return row["id"]

    def _insert_message(self, node: MessageNode, conv_uuid: uuid.UUID, source: Source) -> int:
        msg = node.message
        parent_db_id = None if node.parent_id is None else self._get_db_id(node.parent_id)

        cur = self.conn.execute(
            """INSERT INTO message (uuid, conv_uuid, parent_id, source, role, name, time_ns)
            VALUES (:uuid, :conv_uuid, :parent_id, :source, :role, :name, :time_ns)""",
            {"uuid": str(msg.id), "conv_uuid": str(conv_uuid), "parent_id": parent_db_id,
            "source": int(source), "role": msg.role, "name": msg.name, "time_ns": msg.time_ns},
        )
        msg_db_id = cur.lastrowid

        # Temporary until basic text is stable
        self.conn.execute(
            """INSERT INTO content (message_id, position, type, text)
            VALUES (:message_id, 0, 'text', :text)""",
            {"message_id": msg_db_id, "text": msg.content.text},
        )
        return msg_db_id

    def insert_message_node(self, node: MessageNode, conv: Conversation):
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO conversation (conv_uuid, title, creation_time) "
                "VALUES (?, ?, ?)",
                (str(conv.conv_uuid), conv.title, conv.time_ns),
            )
            self._insert_message(node, conv.conv_uuid, Source.CONVERSATION)

    def insert_conversation(self, conv: Conversation):
        with self.conn:
            self.conn.execute(
                "INSERT INTO conversation (conv_uuid, title, creation_time) VALUES (?, ?, ?)",
                (str(conv.conv_uuid), conv.title, conv.time_ns),
            )
            for node in conv.uuid_index.values():
                self._insert_message(node, conv.conv_uuid, Source.CONVERSATION)

    # magic idk
    def get_conversation(self, conv_uuid: uuid.UUID) -> list[dict]:
        messages = [
            dict(r) for r in self.conn.execute(
                """SELECT m.*, p.uuid AS parent_uuid
                FROM message m
                LEFT JOIN message p ON p.id = m.parent_id
                WHERE m.conv_uuid = ?
                ORDER BY m.id""",
                (str(conv_uuid),),
            )
        ]
        by_id = {m["id"]: m for m in messages}
        for m in messages:
            m["content"] = []

        for c in self.conn.execute(
            """SELECT c.* FROM content c
            JOIN message m ON m.id = c.message_id
            WHERE m.conv_uuid = ?
            ORDER BY c.message_id, c.position""",
            (str(conv_uuid),),
        ):
            by_id[c["message_id"]]["content"].append(dict(c))

        return messages
    
    def __del__(self):
        self.conn.close()
        