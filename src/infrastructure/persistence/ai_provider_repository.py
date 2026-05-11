"""
AI 服务商仓储 - SQLite 实现
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import List, Optional

from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection


class AIProvider:
    def __init__(self, **kwargs):
        self.id: int = kwargs.get("id")
        self.name: str = kwargs.get("name", "")
        self.base_url: str = kwargs.get("base_url", "")
        self.api_key: str = kwargs.get("api_key", "")
        self.model_name: str = kwargs.get("model_name", "")
        self.proxy_url: Optional[str] = kwargs.get("proxy_url")
        self.quota_limit: Optional[int] = kwargs.get("quota_limit")
        self.quota_used: int = kwargs.get("quota_used", 0)
        self.quota_reset_at: Optional[str] = kwargs.get("quota_reset_at")
        self.priority: int = kwargs.get("priority", 0)
        self.enabled: bool = kwargs.get("enabled", True)
        self.created_at: str = kwargs.get("created_at", "")
        self.updated_at: str = kwargs.get("updated_at", "")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model_name": self.model_name,
            "proxy_url": self.proxy_url,
            "quota_limit": self.quota_limit,
            "quota_used": self.quota_used,
            "quota_reset_at": self.quota_reset_at,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def is_quota_exhausted(self) -> bool:
        if self.quota_limit is None:
            return False
        return self.quota_used >= self.quota_limit


def _row_to_provider(row) -> AIProvider:
    data = dict(row)
    data["enabled"] = bool(data["enabled"])
    return AIProvider(**data)


class AIProviderRepository:
    """AI 服务商 CRUD"""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path

    async def find_all(self) -> List[AIProvider]:
        return await asyncio.to_thread(self._find_all_sync)

    async def find_all_enabled(self) -> List[AIProvider]:
        return await asyncio.to_thread(self._find_all_enabled_sync)

    async def find_by_id(self, provider_id: int) -> Optional[AIProvider]:
        return await asyncio.to_thread(self._find_by_id_sync, provider_id)

    async def create(self, data: dict) -> AIProvider:
        return await asyncio.to_thread(self._create_sync, data)

    async def update(self, provider_id: int, data: dict) -> Optional[AIProvider]:
        return await asyncio.to_thread(self._update_sync, provider_id, data)

    async def delete(self, provider_id: int) -> bool:
        return await asyncio.to_thread(self._delete_sync, provider_id)

    async def increment_quota_used(self, provider_id: int) -> None:
        await asyncio.to_thread(self._increment_quota_used_sync, provider_id)

    async def reset_quota(self, provider_id: int) -> None:
        await asyncio.to_thread(self._reset_quota_sync, provider_id)

    def _find_all_sync(self) -> List[AIProvider]:
        bootstrap_sqlite_storage(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM ai_providers ORDER BY priority DESC, id ASC"
            ).fetchall()
        return [_row_to_provider(row) for row in rows]

    def _find_all_enabled_sync(self) -> List[AIProvider]:
        bootstrap_sqlite_storage(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM ai_providers WHERE enabled = 1 ORDER BY priority DESC, id ASC"
            ).fetchall()
        return [_row_to_provider(row) for row in rows]

    def _find_by_id_sync(self, provider_id: int) -> Optional[AIProvider]:
        bootstrap_sqlite_storage(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM ai_providers WHERE id = ?", (provider_id,)
            ).fetchone()
        return _row_to_provider(row) if row else None

    def _create_sync(self, data: dict) -> AIProvider:
        bootstrap_sqlite_storage(self.db_path)
        now = datetime.now().isoformat()
        with sqlite_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO ai_providers (
                    name, base_url, api_key, model_name, proxy_url,
                    quota_limit, quota_used, quota_reset_at, priority, enabled,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """,
                (
                    data["name"],
                    data["base_url"],
                    data["api_key"],
                    data["model_name"],
                    data.get("proxy_url"),
                    data.get("quota_limit"),
                    data.get("quota_reset_at"),
                    data.get("priority", 0),
                    int(data.get("enabled", True)),
                    now,
                    now,
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM ai_providers WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return _row_to_provider(row)

    def _update_sync(self, provider_id: int, data: dict) -> Optional[AIProvider]:
        bootstrap_sqlite_storage(self.db_path)
        now = datetime.now().isoformat()
        fields = []
        values = []
        for key in ("name", "base_url", "api_key", "model_name", "proxy_url",
                    "quota_limit", "quota_reset_at", "priority", "enabled"):
            if key in data:
                val = data[key]
                if key == "enabled":
                    val = int(val)
                fields.append(f"{key} = ?")
                values.append(val)
        if not fields:
            return self._find_by_id_sync(provider_id)
        fields.append("updated_at = ?")
        values.append(now)
        values.append(provider_id)
        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                f"UPDATE ai_providers SET {', '.join(fields)} WHERE id = ?",
                values,
            )
            conn.commit()
        return self._find_by_id_sync(provider_id)

    def _delete_sync(self, provider_id: int) -> bool:
        bootstrap_sqlite_storage(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM ai_providers WHERE id = ?", (provider_id,)
            )
            conn.commit()
        return cursor.rowcount > 0

    def _increment_quota_used_sync(self, provider_id: int) -> None:
        bootstrap_sqlite_storage(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE ai_providers SET quota_used = quota_used + 1, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), provider_id),
            )
            conn.commit()

    def _reset_quota_sync(self, provider_id: int) -> None:
        bootstrap_sqlite_storage(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE ai_providers SET quota_used = 0, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), provider_id),
            )
            conn.commit()
