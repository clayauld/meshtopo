import json
import logging
import sqlite3
from typing import Any, Iterator, MutableMapping, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class PersistentDict(MutableMapping[str, Any]):
    """
    A persistent dictionary backed by SQLite, using JSON serialization.
    Replaces sqlitedict to avoid pickle security vulnerabilities.
    """

    def __init__(
        self,
        filename: str,
        tablename: str = "unnamed",
        autocommit: bool = True,
        encoder: Optional[Any] = None,  # Kept for compatibility but ignored
        decoder: Optional[Any] = None,  # Kept for compatibility but ignored
    ):
        """
        Initialize the persistent dictionary.

        Args:
            filename: Path to the SQLite database file.
            tablename: Name of the table to store data in.
            autocommit: Whether to commit changes automatically (default: True).
            encoder: Ignored, kept for compatibility (always uses json.dumps).
            decoder: Ignored, kept for compatibility (always uses json.loads).
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
        self.conn = sqlite3.connect(self.filename, isolation_level=None)
        # optimize for simple key-value storage
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

    def _create_table(self) -> None:
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
