from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from ...service.authentication.auth import get_current_admin
from ...service.home_management.admin_service import AdminService
from ...service.home_management.models import Admin
from .dependencies import get_admin_service

router = APIRouter(prefix="/home/admin", tags=["home"])


def _serialize_admin(admin: Admin) -> dict:
    """Serialize an Admin for API responses, omitting credential fields."""
    return {
        "id": admin.id,
        "nome": admin.nome,
        "email": admin.email,
        "foto_url": admin.foto_url,
        "descricao": admin.descricao,
        "periodo": admin.periodo,
        "chapa_id": admin.chapa_id,
        "linkedin_url": admin.linkedin_url,
        "git_url": admin.git_url,
        "lattes_url": admin.lattes_url,
    }


@router.post("/", dependencies=[Depends(get_current_admin)])
async def criar_admin(
    nome: str,
    email: str,
    periodo: str,
    chapa_id: int,
    descricao: str,
    foto: UploadFile,
    linkedin_url: str = "",
    git_url: str = "",
    lattes_url: str = "",
    admin_service: AdminService = Depends(get_admin_service),
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
    foto_bytes = await foto.read()

    try:
        admin = admin_service.criar_admin(
            nome=nome,
            email=email,
            periodo=periodo,
            chapa_id=chapa_id,
            foto_bytes=foto_bytes,
            descricao=descricao,
            linkedin_url=linkedin_url,
            git_url=git_url,
            lattes_url=lattes_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _serialize_admin(admin)


@router.delete("/{admin_id}", dependencies=[Depends(get_current_admin)])
def remover_admin(
    admin_id: int,
    admin_service: AdminService = Depends(get_admin_service),
) -> dict:
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
    try:
        admin_service.remover_admin(admin_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {"detail": f"Admin {admin_id} removido com sucesso."}
