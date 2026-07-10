import hashlib
import secrets
import string

def generate_random_password(length: int = 12) -> str:
    """Generate a random password.

    Parameters
    ----------
    length : int, optional
        Password length. Defaults to 8.

    Returns
    -------
    str
        A randomly generated password.
    """
    characters = string.ascii_letters + string.digits + "!@#$%&*._-+"
    return "".join(secrets.choice(characters) for _ in range(length))

def generate_salt() -> str:
    """Generate a random salt.

    Returns
    -------
    str
        A random salt value.
    """
    return secrets.token_hex(16)

def hash_password(password: str, salt: str) -> str:
    """Hash a password with SHA-256 using a salt.

    Parameters
    ----------
    password : str
        Plain-text password.
    salt : str
        Salt value to append before hashing.

    Returns
    -------
    str
        The SHA-256 hash of the salted password.
    """
    salted_password = f"{password}{salt}".encode('utf-8')
    return hashlib.sha256(salted_password).hexdigest()

def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Check whether a password matches the stored hash.

    Parameters
    ----------
    plain_password : str
        Password provided by the user.
    hashed_password : str
        Stored password hash.
    salt : str
        Salt used to generate the stored hash.

    Returns
    -------
    bool
        True if the password matches, otherwise False.
    """
    return hash_password(plain_password, salt) == hashed_password