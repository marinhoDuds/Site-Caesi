from pypika import Query
from sqlalchemy import Engine

from ..database import run_query
from .models import Caesi
from .tables import caesi_table


class CaesiService:
    """Manage the institutional information about CAESI.

    Attributes
    ----------
    engine : Engine
        The database engine used to execute queries.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize a new CaesiService.

        Parameters
        ----------
        engine : Engine
            The database engine used to execute queries.
        """
        self.engine = engine

    def obter_info(self) -> Caesi:
        """Retrieve the current CAESI information, for public display.

        Returns
        -------
        Caesi
            The current CAESI information.

        Raises
        ------
        ValueError
            If no CAESI information is found in the database.
        """
        query = (
            Query.from_(caesi_table)
            .select(caesi_table.id, caesi_table.nome, caesi_table.descricao)
            .limit(1)
        )
        rows = run_query(self.engine, query)

        if not rows:
            raise ValueError("No CAESI information found.")

        row = rows[0]
        return Caesi(id=row.id, nome=row.nome, descricao=row.descricao)

    def atualizar_info(self, nome: str, descricao: str) -> Caesi:
        """Update the CAESI information.

        Parameters
        ----------
        nome : str
            The new name of the entity.
        descricao : str
            The new description or history.

        Returns
        -------
        Caesi
            The updated CAESI information.

        Raises
        ------
        ValueError
            If the update fails or no rows are affected.
        """
        atual = self.obter_info()

        query = (
            Query.update(caesi_table)
            .set(caesi_table.nome, nome)
            .set(caesi_table.descricao, descricao)
            .where(caesi_table.id == atual.id)
        )
        rowcount = run_query(self.engine, query)

        if not rowcount:
            raise ValueError("Failed to update CAESI information.")

        return Caesi(id=atual.id, nome=nome, descricao=descricao)
