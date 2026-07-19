from sqlalchemy import Engine

from .models import Chapa


def create_chapa(engine: Engine, nome: str, ano: int, descricao: str) -> Chapa:
    """Create and persist a new Chapa.

    Parameters
    ----------
    engine : Engine
        The database engine used to execute the query.
    nome : str
        The name of the ticket.
    ano : int
        The effective year of the ticket.
    descricao : str
        The description of proposals or history of the ticket.

    Returns
    -------
    Chapa
        The newly created ticket, including its generated id.
    """


def delete_chapa(engine: Engine, chapa_id: int) -> None:
    """Remove a Chapa by its identifier.

    Parameters
    ----------
    engine : Engine
        The database engine used to execute the query.
    chapa_id : int
        The unique identifier of the ticket to remove.

    Raises
    ------
    ValueError
        If no ticket with the given id exists.
    """


def get_all_chapas(engine: Engine) -> list[Chapa]:
    """Retrieve all registered tickets.

    Parameters
    ----------
    engine : Engine
        The database engine used to execute the query.

    Returns
    -------
    list[Chapa]
        A list containing all tickets currently stored.
    """