import base64
import os
from cryptography import fernet
from aiohttp_session.cookie_storage import EncryptedCookieStorage

print("Testing Fernet.generate_key()...")
key = fernet.Fernet.generate_key()
print(f"Type: {type(key)}, Length: {len(key)}")
try:
    s = EncryptedCookieStorage(key)
    print("Success with Fernet.generate_key()")
except Exception as e:
    print("Error:", e)

print("\nTesting 32 bytes custom key base64 encoded...")
custom_key = b"secret".ljust(32, b"0")[:32]
encoded_custom = base64.urlsafe_b64encode(custom_key)
print(f"Type: {type(encoded_custom)}, Length: {len(encoded_custom)}")
try:
    s = EncryptedCookieStorage(encoded_custom)
    print("Success with encoded custom key")
except Exception as e:
    print("Error:", e)

print("\nTesting 32 bytes RAW custom key...")
print(f"Type: {type(custom_key)}, Length: {len(custom_key)}")
try:
    s = EncryptedCookieStorage(custom_key)
    print("Success with RAW 32 bytes custom key")
except Exception as e:
    print("Error:", e)
