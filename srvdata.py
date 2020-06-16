import sqlite3
import uuid
from typing import Optional

from data import Task, Chat
from db.database import Database, DataRow


def get_task_by_id(database: Database, connection: sqlite3.Connection, id_task: str) -> Task:
    res: Task = Task()
    row: DataRow or None = database.query_row(connection, 'task', id_task)
    res.id_task = uuid.UUID(row.get('id_task'))
    res.chat = get_chat_by_id(database, connection, row.get('id_chat')) if row.get('id_chat') is not None else None
    return res


def get_chat_by_id(database: Database, connection: sqlite3.Connection, id_chat: str) -> Chat:
    res: Chat = Chat()
    row: DataRow or None = database.query_row(connection, 'chat', id_chat)
    res.id_chat = row.get(id_chat)
    res.first_name = row.get('first_name')
    res.last_name = row.get('last_name')
    res.type = row.get('type')
    return res
