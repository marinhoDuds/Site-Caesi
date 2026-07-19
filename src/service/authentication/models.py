from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Payload for email/password login.

    Attributes
    ----------
    email : EmailStr
        Administrator's email.
    password : str
        Administrator's plain-text password.
    """

    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    """Payload for Google OAuth login.

    Attributes
    ----------
    id_token : str
        The ID token returned by Google Sign-In on the frontend.
    """

    id_token: str


class ChangePasswordRequest(BaseModel):
    """Payload to change the authenticated administrator's password.

    Attributes
    ----------
    current_password : str
        The administrator's current password. Required even on the
        mandatory first-login change, so a stolen token alone is not
        enough to take over the account.
    new_password : str
        The new password to set. Must be at least 8 characters long.
    """

    current_password: str
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    """Response returned after a successful authentication.

    Attributes
    ----------
    access_token : str
        The signed JWT access token.
    token_type : str
        The token type, always "bearer".
    must_change_password : bool
        True if the frontend must redirect to the change-password
        screen before allowing access to the rest of the panel.
    """

    access_token: str
    token_type: str = "bearer"
    must_change_password: bool


class AdminOut(BaseModel):
    """Public representation of an administrator.

    Attributes
    ----------
    id : int
        The administrator's ID.
    name : str
        The administrator's name.
    email : str
        The administrator's email.
    """

    id: int
    name: str
    email: str