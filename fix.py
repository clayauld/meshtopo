import re

with open("src/web/auth.py", "r") as f:
    content = f.read()

content = "import binascii\n" + content

with open("src/web/auth.py", "w") as f:
    f.write(content)
