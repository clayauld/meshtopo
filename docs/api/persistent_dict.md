# Module `persistent_dict`

## Classes

## `class PersistentDict`

A persistent dictionary backed by SQLite, using JSON serialization.
Replaces sqlitedict to avoid pickle security vulnerabilities.

### `def __init__(self, filename: str, tablename: str = 'unnamed', autocommit: bool = True, encoder: Optional[Any] = None, decoder: Optional[Any] = None)`

Initialize the persistent dictionary.

Args:
    filename: Path to the SQLite database file.
    tablename: Name of the table to store data in.
    autocommit: Whether to commit changes automatically (default: True).
    encoder: Ignored, kept for compatibility (always uses json.dumps).
    decoder: Ignored, kept for compatibility (always uses json.loads).

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

### `def pop(self, key, default=<object object at 0x...>)`

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
