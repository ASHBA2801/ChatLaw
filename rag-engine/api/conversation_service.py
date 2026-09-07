"""Persistence boundary for conversations and messages."""

import json
import secrets
import time
from typing import Any


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _message(row: Any) -> dict[str, Any]:
    row = dict(row) if hasattr(row, "keys") else dict(zip(
        ("id", "role", "content", "language", "metadata", "created_at"), row))
    return {**row, "created_at": _iso(row["created_at"]), "metadata": row.get("metadata")}


def _new_id() -> str:
    """Generate a database-side application ID without exposing ID creation to the browser."""
    timestamp = format(int(time.time() * 1000), "x")
    return f"c{timestamp}{secrets.token_hex(10)}"


class ConversationStore:
    def __init__(self, connection):
        self.connection = connection

    def create(self, case_id: str | None = None, user_id: str | None = None) -> dict[str, str | None]:
        cursor = self.connection.cursor()
        cursor.execute(
            '''INSERT INTO "conversations" ("id", "caseId", "userId", "createdAt", "updatedAt")
               VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
               RETURNING "id", "caseId", "userId", "createdAt", "updatedAt"''',
            (_new_id(), case_id, user_id),
        )
        row = cursor.fetchone()
        self.connection.commit()
        return {
            "id": row[0],
            "case_id": row[1],
            "user_id": row[2],
            "created_at": _iso(row[3]),
            "updated_at": _iso(row[4]),
        }

    def exists(self, conversation_id: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute('SELECT 1 FROM "conversations" WHERE "id" = %s', (conversation_id,))
        return cursor.fetchone() is not None

    def list(self) -> list[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute('''SELECT c."id", c."createdAt", c."updatedAt",
            (SELECT m."content" FROM "messages" m WHERE m."conversationId" = c."id" AND m."role" = 'user'
             ORDER BY m."createdAt" ASC LIMIT 1) AS title
            FROM "conversations" c ORDER BY c."updatedAt" DESC''')
        return [{"id": row[0], "title": _title(row[3]), "created_at": _iso(row[1]), "updated_at": _iso(row[2])}
                for row in cursor.fetchall()]

    def get(self, conversation_id: str) -> dict[str, Any] | None:
        cursor = self.connection.cursor()
        cursor.execute('SELECT "id", "createdAt", "updatedAt" FROM "conversations" WHERE "id" = %s', (conversation_id,))
        conversation = cursor.fetchone()
        if conversation is None:
            return None
        cursor.execute('''SELECT "id", "role", "content", "language", "metadata", "createdAt"
                         FROM "messages" WHERE "conversationId" = %s ORDER BY "createdAt" ASC''', (conversation_id,))
        messages = [_message(row) for row in cursor.fetchall()]
        return {"id": conversation[0], "title": _title(next((m["content"] for m in messages if m["role"] == "user"), None)),
                "created_at": _iso(conversation[1]), "updated_at": _iso(conversation[2]), "messages": messages}

    def recent_messages(self, conversation_id: str, limit: int = 8) -> list[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute('''SELECT "role", "content" FROM "messages" WHERE "conversationId" = %s
                         ORDER BY "createdAt" DESC LIMIT %s''', (conversation_id, limit))
        return [{"role": row[0], "content": row[1]} for row in reversed(cursor.fetchall())]

    def last_assistant_metadata(self, conversation_id: str) -> dict[str, Any] | None:
        cursor = self.connection.cursor()
        cursor.execute(
            '''SELECT "metadata" FROM "messages"
               WHERE "conversationId" = %s AND "role" = 'assistant'
               ORDER BY "createdAt" DESC LIMIT 1''',
            (conversation_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        metadata = row[0]
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                return None
        return metadata if isinstance(metadata, dict) else None

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        cursor = self.connection.cursor()
        cursor.execute(
            '''INSERT INTO "messages" ("id", "conversationId", "role", "content", "language", "metadata")
               VALUES (%s, %s, %s, %s, %s, %s::jsonb)
               RETURNING "id", "role", "content", "language", "metadata", "createdAt"''',
            (
                _new_id(),
                conversation_id,
                role,
                content,
                language or "en",
                json.dumps(metadata) if metadata is not None else None,
            ),
        )
        row = cursor.fetchone()
        cursor.execute('UPDATE "conversations" SET "updatedAt" = CURRENT_TIMESTAMP WHERE "id" = %s', (conversation_id,))
        self.connection.commit()
        return _message(row)

    def delete(self, conversation_id: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM "conversations" WHERE "id" = %s', (conversation_id,))
        deleted = cursor.rowcount > 0
        self.connection.commit()
        return deleted


def _title(content: str | None) -> str:
    if not content:
        return "New conversation"
    title = " ".join(content.split())
    if title.lower().startswith("what is "):
        title = title[8:]
    return title[:60] + ("…" if len(title) > 60 else "")