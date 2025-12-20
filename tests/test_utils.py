from utils import sanitize_for_log


class TestSanitizeForLog:
    def test_sanitize_clean_string(self):
        assert sanitize_for_log("clean string") == "clean string"

    def test_sanitize_newlines(self):
        assert sanitize_for_log("line1\nline2") == "line1\\x0aline2"
        assert sanitize_for_log("line1\rline2") == "line1\\x0dline2"

    def test_sanitize_printable_objects(self):
        assert sanitize_for_log(123) == "123"
        assert sanitize_for_log(12.34) == "12.34"

    def test_sanitize_bytes(self):
        # Bytes repr is printable
        assert sanitize_for_log(b"bytes") == "b'bytes'"
        # Repr of bytes already escapes newlines
        assert sanitize_for_log(b"line1\nline2") == "b'line1\\nline2'"

    def test_sanitize_none(self):
        assert sanitize_for_log(None) == "None"

    def test_sanitize_list(self):
        # Repr of list already escapes newlines in strings
        # "['a', 'b\\n']" is printable
        assert sanitize_for_log(["a", "b\n"]) == "['a', 'b\\n']"

    def test_complex_injection_attempt(self):
        # Simulate a log injection attack string
        attack = "User logged in\n[INFO] User became admin"
        sanitized = sanitize_for_log(attack)
        assert sanitized == "User logged in\\x0a[INFO] User became admin"
        assert "\n" not in sanitized
