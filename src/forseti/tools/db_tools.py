"""DB Tools for data verification — Sprint 05.

Provides database adapters to verify data after API calls.
"""
from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod


class DBAdapter(ABC):
    """Abstract base for database adapters."""

    @abstractmethod
    def query(self, sql: str) -> list[dict]:
        """Execute a query and return rows as dicts."""

    def close(self) -> None:
        """Cleanup resources."""


class NoneAdapter(DBAdapter):
    """No-op adapter for projects without DB verification."""

    def query(self, sql: str) -> list[dict]:
        return []


class SQLiteAdapter(DBAdapter):
    """SQLite adapter for local DB verification."""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def query(self, sql: str) -> list[dict]:
        rows = self.conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()


def create_db_adapter(adapter_type: str, config: dict) -> DBAdapter:
    """Create a DB adapter based on type.

    Supported types: none, sqlite, firestore (future).
    """
    if adapter_type == "none":
        return NoneAdapter()
    elif adapter_type == "sqlite":
        return SQLiteAdapter(db_path=config["db_path"])
    else:
        raise ValueError(f"Unknown db adapter: {adapter_type}")
