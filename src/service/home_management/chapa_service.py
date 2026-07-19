from pypika import Query, QmarkParameter
from sqlalchemy import Engine, text

from ..database import run_query
from .models import Chapa
from .tables import chapa_table


def _insert_and_get_id(engine: Engine, query) -> int:
    """Execute an INSERT query on its own connection and return the new id.

    ``database.run_query`` returns the affected row count for statements
    that don't return rows, which isn't enough to build the created
    object. This mirrors its parameter-binding logic but keeps the
    cursor's ``lastrowid`` (populated by the MySQL driver) instead.
    """
    param_handler = QmarkParameter()
    sql_query = query.get_sql(parameter=param_handler)
    parameters = param_handler.get_parameters()

    with engine.connect() as conn:
        result = conn.execute(text(sql_query), parameters)
        conn.commit()
        return result.lastrowid


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
    query = (
        Query.into(chapa_table)
        .columns("nome", "ano", "descricao")
        .insert(nome, ano, descricao)
    )
    chapa_id = _insert_and_get_id(engine, query)

    return Chapa(id=chapa_id, nome=nome, ano=ano, descricao=descricao)


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
    query = Query.from_(chapa_table).where(chapa_table.id == chapa_id).delete()
    rowcount = run_query(engine, query)

    if not rowcount:
        raise ValueError(f"No chapa found with id {chapa_id}.")


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
    query = Query.from_(chapa_table).select(
        chapa_table.id, chapa_table.nome, chapa_table.ano, chapa_table.descricao
    )
    rows = run_query(engine, query)

    return [
        Chapa(id=row.id, nome=row.nome, ano=row.ano, descricao=row.descricao)
        for row in rows
    ]
