from fastapi import APIRouter, Depends, UploadFile

router = APIRouter(prefix="/home/admin", tags=["home"])


@router.post("/", dependencies=[Depends()])
def criar_admin(
    nome: str,
    email: str,
    periodo: str,
    chapa_id: int,
    descricao: str,
    foto: UploadFile,
    linkedin_url: str = "",
    git_url: str = "",
    lattes_url: str = "",
) -> dict:
    """Register a new Admin. Requires admin authentication.

    Parameters
    ----------
    nome : str
        The admin's name.
    email : str
        The admin's email.
    periodo : str
        The academic term.
    chapa_id : int
        The ID of the linked ticket.
    descricao : str
        The admin's description.
    foto : UploadFile
        The admin's photo file to upload.
    linkedin_url : str, optional
        The admin's LinkedIn profile URL.
    git_url : str, optional
        The admin's GitHub profile URL.
    lattes_url : str, optional
        The admin's Lattes curriculum URL.

    Returns
    -------
    dict
        The newly created admin serialized as JSON.
    """


@router.delete("/{admin_id}", dependencies=[Depends()])
def remover_admin(admin_id: int) -> dict:
    """Remove an Admin by its identifier. Requires admin authentication.

    Parameters
    ----------
    admin_id : int
        The unique identifier of the admin to remove.

    Returns
    -------
    dict
        A confirmation message.
    """
