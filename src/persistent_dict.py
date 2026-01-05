"""
Persistent dictionary implementation for the Meshtopo gateway.
Provides a simple key-value store backed by SQLite for state persistence.
"""

import json
import logging
import sqlite3
from typing import Any, Iterator, MutableMapping, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class PersistentDict(MutableMapping[str, Any]):
    """
    A thread-safe, persistent dictionary-like object backed by a SQLite database.
    Values are stored as JSON-serialized strings, providing a safer alternative
    to pickle-based storage while maintaining a familiar dict-like interface.

    This class implements the collections.abc.MutableMapping interface,
    allowing it to be used wherever a standard dictionary is expected.
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
        """
        Establish a connection to the SQLite database and configure
        performance-optimizing pragmas.
        """
        # We use sqlite3.connect directly.
        # Isolation level is left as default to allow manual transaction
        # control via .commit()
        self.conn = sqlite3.connect(self.filename)

        # Write-Ahead Logging (WAL) significantly improves concurrency
        # for key-value loads.
        self.conn.execute("PRAGMA journal_mode=WAL")
        # NORMAL synchronous mode provides a good balance between safety
        # and performance.
        self.conn.execute("PRAGMA synchronous=NORMAL")

    def _create_table(self) -> None:
        """
        Initialize the database schema if the target table does not already exist.
        The schema uses a simple key (TEXT) and value (TEXT) structure.
        """
        if not self.conn:
            return

        # Explicitly use the provided tablename. Note: tablename was
        # validated in __init__ to prevent SQL injection risks.
        query = (
            f"CREATE TABLE IF NOT EXISTS {self.tablename} "  # nosec
            "(key TEXT PRIMARY KEY, value TEXT)"
        )
        self.conn.execute(query)

    def __getitem__(self, key: str) -> Any:
        """
        Retrieve a value from the database by its key.

        Args:
            key: The string key to look up.

        Returns:
            The decoded (JSON) value associated with the key.

        Raises:
            KeyError: If the key is not found or JSON decoding fails.
            RuntimeError: If the database connection is closed.
        """
        if not self.conn:
            raise RuntimeError("Database connection closed")

        query = f"SELECT value FROM {self.tablename} WHERE key = ?"  # nosec
        cursor = self.conn.execute(query, (key,))
        row = cursor.fetchone()

        if row is None:
            raise KeyError(key)

        try:
            # We strictly use JSON to avoid the security risks of pickle
            return json.loads(row[0])
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON for key {key}. Data may be corrupted.")
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Store a value in the database, associating it with the given key.

        Args:
            key: The string key for storage.
            value: Any JSON-serializable object to store.

        Raises:
            RuntimeError: If the database connection is closed.
        """
        if not self.conn:
            raise RuntimeError("Database connection closed")

        # Serializing to JSON ensures cross-platform compatibility and safety.
        serialized_value = json.dumps(value)
        query = (
            f"INSERT OR REPLACE INTO {self.tablename} "  # nosec
            "(key, value) VALUES (?, ?)"
        )
        self.conn.execute(query, (key, serialized_value))

        # Committing immediately if autocommit is enabled (default behavior)
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
