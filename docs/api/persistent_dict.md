# Module `persistent_dict`

Persistent dictionary implementation for the Meshtopo gateway.
Provides a simple key-value store backed by SQLite for state persistence.

## Classes

## `class PersistentDict`

A thread-safe, persistent dictionary-like object backed by a SQLite database.
Values are stored as JSON-serialized strings, providing a safer alternative
to pickle-based storage while maintaining a familiar dict-like interface.

This class implements the collections.abc.MutableMapping interface,
allowing it to be used wherever a standard dictionary is expected.

### `def __init__(self, filename: str, tablename: str = 'unnamed', autocommit: bool = True, encoder: Optional[Any] = None, decoder: Optional[Any] = None)`

Initialize the persistent dictionary.

Args:
    filename: Path to the SQLite database file.
    tablename: Name of the table to store data in.
    autocommit: Whether to commit changes automatically (default: True).
    encoder: Ignored, kept for compatibility (always uses json.dumps).
    decoder: Ignored, kept for compatibility (always uses json.loads).

### `def _connect(self) -> None`

Establish a connection to the SQLite database and configure
performance-optimizing pragmas.

### `def _create_table(self) -> None`

Initialize the database schema if the target table does not already exist.
The schema uses a simple key (TEXT) and value (TEXT) structure.

### `def close(self) -> None`

Close the database connection.
