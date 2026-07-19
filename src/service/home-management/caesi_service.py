from sqlalchemy import Engine

from .models import Caesi


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
