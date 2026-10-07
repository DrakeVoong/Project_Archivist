import sqlite3
import uuid
from typing import List
from enum import IntEnum

from archivist.config.settings import CONV_PATH
from archivist.core.message import Message, MessageNode, UserMessage, AssistantMessage
from archivist.memory.conversation import Conversation


class Source(IntEnum):
    CONVERSATION = 1
    SUMMARY = 2
    MEMORY = 3

class SQLDB:
    def __init__(self):
        self._connect()
        self._create_tables()
        self._seed_lookup_tables()

    def _connect(self):
        db_path = CONV_PATH / "conversations.db"
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _seed_lookup_tables(self):
        # Source
        query = "INSERT OR IGNORE INTO source (id, name) VALUES (?, ?)"
        for s in Source:
            self.cursor.execute(query, (s.value, s.name.lower()))

    def _create_tables(self):

        # Source
        # What type of message it is (conversation, memory, summary, etc.)
        query = """CREATE TABLE IF NOT EXISTS source (
            id              INTEGER PRIMARY KEY,
            name            TEXT NOT NULL UNIQUE
        )"""
        self.cursor.execute(query)

        # Message Dataclass
        query = """CREATE TABLE IF NOT EXISTS message (
            id              INTEGER PRIMARY KEY,
            uuid            TEXT NOT NULL,
            source          INTEGER NOT NULL REFERENCES source(id),
            name            TEXT NOT NULL,
            content         TEXT NOT NULL,
            time            INTEGER NOT NULL
        )"""
        self.cursor.execute(query)

        # Conversation
        # Data about a conversation
        query = """CREATE TABLE IF NOT EXISTS conversation (
            conv_uuid       TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            creation_time   INTEGER NOT NULL
        )"""
        self.cursor.execute(query)

        # Conv
        # Individual message in a conversation
        query = """CREATE TABLE IF NOT EXISTS conv (
            message_id      INTEGER PRIMARY KEY REFERENCES message(id),
            conv_uuid       TEXT NOT NULL REFERENCES conversation(conv_uuid),
            parent_id       INTEGER REFERENCES conv(message_id)
        )"""
        self.cursor.execute(query)

        # Faster searches when looking up entire conversation messages
        query = "CREATE INDEX IF NOT EXISTS idx_conv_uuid ON conv(conv_uuid)"
        self.cursor.execute(query)

        # Assistant Dataclass
        query = """CREATE TABLE IF NOT EXISTS assistant_message (
            message_id      INTEGER PRIMARY KEY REFERENCES message(id),
            model           TEXT NOT NULL,
            provider        TEXT NOT NULL,
            finish_reason   TEXT NOT NULL DEFAULT ''
        )"""
        self.cursor.execute(query)

        # Tool Dataclass
        query = """CREATE TABLE IF NOT EXISTS tool_message (
            message_id      INTEGER PRIMARY KEY REFERENCES message(id),
            success         INTEGER NOT NULL DEFAULT 0,
            retry           INTEGER NOT NULL DEFAULT 0
        )"""
        self.cursor.execute(query)

    def get_conversation(self, conv_id: uuid.UUID) -> list:
        self.cursor.execute("SELECT * FROM message WHERE conv_id = (:conv_id)"
                            , {"conv_id":conv_id})

        result = self.cursor.fetchall()
        return result

    def _insert_message(self, message:Message, source:Source, continuous_commit:bool = False):
            with self.conn:
                self.cursor.execute("INSERT INTO message (uuid, source, name, content, time) " \
                                    "VALUES(:uuid, :source, :name, :content, :time)"
                                    , {"uuid":str(message.id), "source":source.value, "name":message.name,
                                    "content":message.content, "time":message.time})
                id = self.cursor.lastrowid
            return id

    def insert_message_node(self, message_node:MessageNode, conv:Conversation):
        with self.conn:
            message_id = self._insert_message(message_node.message, Source.CONVERSATION, continuous_commit=True)
            
            self.cursor.execute("INSERT INTO conversation (conv_uuid, title, creation_time)" \
                                "VALUES(:conv_uuid, :title, :creation_time)",
                                {"conv_uuid":str(conv.conv_id), "title":conv.title, "creation_time":str(conv.time)}
                                )
            
            self.cursor.execute("INSERT INTO conv (message_id, conv_uuid, parent_id)" \
                                "VALUES(:message_id, :conv_uuid, :parent_id)",
                                {"message_id":message_id, "conv_uuid":str(conv.conv_id), "parent_id":None})

    def del_table(self):
        self.cursor.execute("DELETE FROM message")
        self.conn.commit()

    def __del___(self):
        self.conn.close()
        