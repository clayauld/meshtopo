# Module `persistent_dict`

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

* **WAL Mode:** The database is configured in Write-Ahead Logging (WAL) mode.
    This allows for better concurrency, as readers do not block writers.
* **Synchronous Normal:** We use `PRAGMA synchronous=NORMAL` for a good balance
    between performance and durability.

## Usage

    d = PersistentDict("my_db.sqlite", tablename="users")
    d["key"] = {"some": "json", "data": 123}
    d.close()

## Classes

## `class PersistentDict`

A persistent dictionary backed by SQLite, using strict JSON serialization.

### `def __init__(self, filename: str, tablename: str = 'unnamed', autocommit: bool = True, encoder: Optional[Any] = None, decoder: Optional[Any] = None)`

Initialize the persistent dictionary.

Args:
    filename: Path to the SQLite database file.
    tablename: Name of the table to store data in. Must be alphanumeric.
    autocommit: Whether to commit changes automatically (default: True).

### `def clear(self)`

D.clear() -> None.  Remove all items from D.

### `def close(self) -> None`

Close the database connection.

### `def get(self, key, default=None)`

D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.

### `def items(self)`

D.items() -> a set-like object providing a view on D's items

### `def keys(self)`

D.keys() -> a set-like object providing a view on D's keys

### `def pop(self, key, default=<object object at 0x7a58119781e0>)`

D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
If key is not found, d is returned if given, otherwise KeyError is raised.

### `def popitem(self)`

D.popitem() -> (k, v), remove and return some (key, value) pair
as a 2-tuple; but raise KeyError if D is empty.

### `def setdefault(self, key, default=None)`

D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D

### `def update(self, other=(), /, **kwds)`

D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
If E present and has a .keys() method, does:     for k in E.keys(): D[k] = E[k]
If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
In either case, this is followed by: for k, v in F.items(): D[k] = v

### `def values(self)`

D.values() -> an object providing a view on D's values
