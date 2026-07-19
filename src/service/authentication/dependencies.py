from fastapi import Depends, HTTPException, status

from src.service.authentication.auth import get_current_admin


def get_active_admin(admin: dict = Depends(get_current_admin)) -> dict:
    """Require an administrator who has already completed the mandatory
    first-login password change.

    Use this dependency (instead of `get_current_admin`) on every panel
    route that exposes management features, so an administrator cannot
    use the system before setting their own password. The only route
    that should keep using `get_current_admin` directly is the
    change-password endpoint itself.

    Parameters
    ----------
    admin : dict
        The authenticated administrator, injected by `get_current_admin`.

    Returns
    -------
    dict
        The same admin dict, unchanged.

    Raises
    ------
    HTTPException
        403 if the administrator still has a pending password change.
    """
    if admin.get("must_change_password"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required before accessing this resource",
        )
    return admin
