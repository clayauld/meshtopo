import sqlite3

import pytest

from persistent_dict import PersistentDict


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


def test_init_creates_table(db_path):
    pd = PersistentDict(db_path, tablename="test_table")
    pd.close()

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
    )
    assert cursor.fetchone()[0] == "test_table"
    conn.close()


def test_set_get_item(db_path):
    with PersistentDict(db_path) as pd:
        pd["key1"] = "value1"
        pd["key2"] = {"nested": "dict", "list": [1, 2, 3]}

        assert pd["key1"] == "value1"
        assert pd["key2"] == {"nested": "dict", "list": [1, 2, 3]}


def test_get_item_missing_key(db_path):
    with PersistentDict(db_path) as pd:
        with pytest.raises(KeyError):
            _ = pd["missing"]


def test_del_item(db_path):
    with PersistentDict(db_path) as pd:
        pd["key1"] = "value1"
        assert "key1" in pd

        del pd["key1"]
        assert "key1" not in pd

        with pytest.raises(KeyError):
            del pd["missing"]


def test_len_and_iter(db_path):
    with PersistentDict(db_path) as pd:
        pd["k1"] = "v1"
        pd["k2"] = "v2"
        pd["k3"] = "v3"

        assert len(pd) == 3
        assert set(pd) == {"k1", "k2", "k3"}


def test_persistence(db_path):
    # Write data
    pd1 = PersistentDict(db_path)
    pd1["persist"] = "true"
    pd1.close()

    # Read data from new instance
    pd2 = PersistentDict(db_path)
    assert pd2["persist"] == "true"
    pd2.close()


def test_json_serialization_only(db_path):
    """Verify that it stores valid JSON string in the DB"""
    with PersistentDict(db_path, tablename="json_test") as pd:
        pd["foo"] = "bar"

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT value FROM json_test WHERE key='foo'")
    raw_value = cursor.fetchone()[0]
    conn.close()

    # Check that it stored a JSON string
    assert raw_value == '"bar"'


def test_invalid_json_in_db(db_path):
    """Verify handling of non-JSON data (e.g. if file corrupted or migration needed)"""
    # Manually insert bad data
    conn = sqlite3.connect(db_path)
    tablename = "test"  # Define tablename for clarity
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {tablename} (key TEXT PRIMARY KEY, value TEXT)"
    )
    # Manually corrupt the DB with non-JSON data
    conn.execute(
        f"INSERT INTO {tablename} (key, value) VALUES (?, ?)", ("bad_key", "{invalid")
    )
    conn.commit()
    conn.close()

    with PersistentDict(db_path, tablename="test") as pd:
        # Should raise KeyError on decode failure (as per implementation)
        # or JSONDecodeError
        with pytest.raises(KeyError):
            _ = pd["bad_key"]
