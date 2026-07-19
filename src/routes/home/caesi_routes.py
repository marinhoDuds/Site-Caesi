from fastapi import APIRouter, Depends

router = APIRouter(prefix="/home/caesi", tags=["home"])


@router.get("/")
def obter_info_caesi() -> dict:
    """Retrieve the current CAESI information. Public route.

    Returns
    -------
    dict
        The CAESI information serialized as JSON.
    """


@router.put("/", dependencies=[Depends()])
def atualizar_info_caesi(nome: str, descricao: str) -> dict:
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
