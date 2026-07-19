from fastapi import APIRouter, Depends

router = APIRouter(prefix="/home/chapa", tags=["home"])


@router.post("/", dependencies=[Depends()])
def criar_chapa(nome: str, ano: int, descricao: str) -> dict:
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


@router.delete("/{chapa_id}", dependencies=[Depends()])
def remover_chapa(chapa_id: int) -> dict:
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


@router.get("/")
def listar_chapas() -> list[dict]:
    """Retrieve all registered tickets. Public route.

    Returns
    -------
    list[dict]
        A list of tickets, each including their associated admins,
        serialized as JSON.
    """