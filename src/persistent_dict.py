"""
Secure Persistent Dictionary

This module implements a persistent key-value store backed by SQLite.
It is a replacement for `sqlitedict` specifically designed to avoid the
security risks associated with Python's `pickle` serialization.

## Security Rationale
The `sqlitedict` library defaults to using `pickle` for serialization.
Pickle is unsafe when deserializing data from untrusted sources, as it can
execute arbitrary code. While `sqlitedict` supports JSON, mixing it
into a codebase with pickle defaults is risky. This class enforces
JSON serialization/deserialization strictly.

## Performance
*   **WAL Mode:** The database is configured in Write-Ahead Logging (WAL) mode.
    This allows for better concurrency, as readers do not block writers.
*   **Synchronous Normal:** We use `PRAGMA synchronous=NORMAL` for a good balance
    between performance and durability.

## Usage
    d = PersistentDict("my_db.sqlite", tablename="users")
    d["key"] = {"some": "json", "data": 123}
    d.close()
"""

import json
import logging
import sqlite3
from typing import Any, Iterator, MutableMapping, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class PersistentDict(MutableMapping[str, Any]):
    """
    A persistent dictionary backed by SQLite, using strict JSON serialization.
    """

    def __init__(
        self,
        filename: str,
        tablename: str = "unnamed",
        autocommit: bool = True,
        encoder: Optional[Any] = None,  # Kept for interface compatibility but ignored
        decoder: Optional[Any] = None,  # Kept for interface compatibility but ignored
    ):
        """
        Initialize the persistent dictionary.

        Args:
            filename: Path to the SQLite database file.
            tablename: Name of the table to store data in. Must be alphanumeric.
            autocommit: Whether to commit changes automatically (default: True).
        """
        self.filename = filename
        if not tablename.replace("_", "").isalnum():
            raise ValueError("Tablename must be alphanumeric")
        self.tablename = tablename
        self.autocommit = autocommit
        self.conn: Optional[sqlite3.Connection] = None

        self._connect()
        self._create_table()

    def _connect(self) -> None:
        """Establish connection and configure PRAGMAs."""
        # Use default isolation level to allow manual transaction control if needed
        self.conn = sqlite3.connect(self.filename)

        # Performance tuning
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

    def _create_table(self) -> None:
        """Create the KV table if it doesn't exist."""
        if not self.conn:
            return
        query = (
            f"CREATE TABLE IF NOT EXISTS {self.tablename} "  # nosec
            "(key TEXT PRIMARY KEY, value TEXT)"
        )
        self.conn.execute(query)

    def __getitem__(self, key: str) -> Any:
        if not self.conn:
            raise RuntimeError("Database connection closed")

        query = f"SELECT value FROM {self.tablename} WHERE key = ?"  # nosec
        cursor = self.conn.execute(query, (key,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(key)

        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON for key {key}")
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if not self.conn:
            raise RuntimeError("Database connection closed")

        # Strict JSON serialization
        serialized_value = json.dumps(value)
        query = (
            f"INSERT OR REPLACE INTO {self.tablename} "  # nosec
            "(key, value) VALUES (?, ?)"
        )
        self.conn.execute(query, (key, serialized_value))
        if self.autocommit:
            self.conn.commit()

    def __delitem__(self, key: str) -> None:
        if not self.conn:
            raise RuntimeError("Database connection closed")

        if key not in self:
            raise KeyError(key)

        query = f"DELETE FROM {self.tablename} WHERE key = ?"  # nosec
        self.conn.execute(query, (key,))
        if self.autocommit:
            self.conn.commit()

    def __iter__(self) -> Iterator[str]:
        if not self.conn:
            raise RuntimeError("Database connection closed")

        query = f"SELECT key FROM {self.tablename}"  # nosec
        cursor = self.conn.execute(query)
        for row in cursor:
            yield row[0]

    def __len__(self) -> int:
        if not self.conn:
            raise RuntimeError("Database connection closed")

        query = f"SELECT COUNT(*) FROM {self.tablename}"  # nosec
        cursor = self.conn.execute(query)
        result = cursor.fetchone()
        return result[0] if result else 0

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "PersistentDict":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
