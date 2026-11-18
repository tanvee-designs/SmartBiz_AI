
from getpass import getpass
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

password = getpass("Enter a strong Admin password: ")
confirm = getpass("Confirm Admin password: ")

if password != confirm:
    raise SystemExit("Passwords do not match.")

if len(password) < 12:
    raise SystemExit("Use a password with at least 12 characters.")

hashed_password = password_hash.hash(password)

print("\nAdmin password hash:\n")
print(hashed_password)
