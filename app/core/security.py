import bcrypt


# Turns a plain password into a bcrypt hash we can safely store.
def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


# Checks a typed password against a stored bcrypt hash.
def check_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
