from fastapi import APIRouter, Depends, HTTPException, status

from ...service.authentication.auth import get_current_admin
from ...service.home_management.admin_service import AdminService
from ...service.home_management.models import Admin, Chapa
from .dependencies import get_admin_service

router = APIRouter(prefix="/home/chapa", tags=["home"])


def _serialize_admin_resumo(admin: Admin) -> dict:
    """Serialize an Admin nested inside a Chapa, omitting credentials."""
    return {
        "id": admin.id,
        "nome": admin.nome,
        "email": admin.email,
        "foto_url": admin.foto_url,
        "descricao": admin.descricao,
        "periodo": admin.periodo,
        "linkedin_url": admin.linkedin_url,
        "git_url": admin.git_url,
        "lattes_url": admin.lattes_url,
    }


def _serialize_chapa(chapa: Chapa, admin_service: AdminService) -> dict:
    """Serialize a Chapa for API responses, nesting its admins."""
    admins = admin_service.listar_admins_por_chapa(chapa.id)
    return {
        "id": chapa.id,
        "nome": chapa.nome,
        "ano": chapa.ano,
        "descricao": chapa.descricao,
        "admins": [_serialize_admin_resumo(admin) for admin in admins],
    }


@router.post("/", dependencies=[Depends(get_current_admin)])
def criar_chapa(
    nome: str,
    ano: int,
    descricao: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> dict:
    """Register a new Chapa. Requires admin authentication.

    Parameters
    ----------
    nome : str
        The name of the ticket.
    ano : int
        The effective year of the ticket.
    descricao : str
        The description of the ticket.

    Returns
    -------
    dict
        The newly created ticket serialized as JSON.
    """
    chapa = admin_service.criar_chapa(nome, ano, descricao)
    return _serialize_chapa(chapa, admin_service)


@router.delete("/{chapa_id}", dependencies=[Depends(get_current_admin)])
def remover_chapa(
    chapa_id: int,
    admin_service: AdminService = Depends(get_admin_service),
) -> dict:
    """Remove a Chapa by its identifier. Requires admin authentication.

    Parameters
    ----------
    chapa_id : int
        The unique identifier of the ticket to remove.

    Returns
    -------
    dict
        A confirmation message.
    """
    try:
        admin_service.remover_chapa(chapa_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"detail": f"Chapa {chapa_id} removida com sucesso."}


@router.get("/")
def listar_chapas(
    admin_service: AdminService = Depends(get_admin_service),
) -> list[dict]:
    """Retrieve all registered tickets. Public route.

    Returns
    -------
    list[dict]
        A list of tickets, each including their associated admins,
        serialized as JSON.
    """
    chapas = admin_service.listar_chapas()
    return [_serialize_chapa(chapa, admin_service) for chapa in chapas]
