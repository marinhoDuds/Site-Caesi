from fastapi import APIRouter, Depends, HTTPException, status

from ...service.authentication.auth import get_current_admin
from ...service.home_management.caesi_service import CaesiService
from ...service.home_management.models import Caesi
from .dependencies import get_caesi_service

router = APIRouter(prefix="/home/caesi", tags=["home"])


def _serialize_caesi(caesi: Caesi) -> dict:
    """Serialize a Caesi object for API responses."""
    return {"id": caesi.id, "nome": caesi.nome, "descricao": caesi.descricao}


@router.get("/")
def obter_info_caesi(
    caesi_service: CaesiService = Depends(get_caesi_service),
) -> dict:
    """Retrieve the current CAESI information. Public route.

    Returns
    -------
    dict
        The CAESI information serialized as JSON.
    """
    try:
        caesi = caesi_service.obter_info()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return _serialize_caesi(caesi)


@router.put("/", dependencies=[Depends(get_current_admin)])
def atualizar_info_caesi(
    nome: str,
    descricao: str,
    caesi_service: CaesiService = Depends(get_caesi_service),
) -> dict:
    """Update the CAESI information. Requires admin authentication.

    Parameters
    ----------
    nome : str
        The new name of the entity.
    descricao : str
        The new description or history.

    Returns
    -------
    dict
        The updated CAESI information serialized as JSON.
    """
    try:
        caesi = caesi_service.atualizar_info(nome, descricao)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _serialize_caesi(caesi)
