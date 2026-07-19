from sqlalchemy import Engine

from .models import Admin, Chapa
from .password_service import PasswordService
from .storage_service import StorageService
from .email_service import EmailService


class AdminService:
    """Coordinate operations over admins and tickets (chapas).

    Orchestrates PasswordService, StorageService and EmailService to
    fulfil the administrator user stories of the Quem Somos module.

    Attributes
    ----------
    engine : Engine
        The database engine used to execute queries.
    password_service : PasswordService
        Service used to generate and hash admin passwords.
    storage_service : StorageService
        Service used to upload and remove admin photos.
    email_service : EmailService
        Service used to notify admins of their generated password.
    """

    def __init__(
        self,
        engine: Engine,
        password_service: PasswordService,
        storage_service: StorageService,
        email_service: EmailService,
    ) -> None:
        """Initialize a new AdminService.

        Parameters
        ----------
        engine : Engine
            The database engine used to execute queries.
        password_service : PasswordService
            Service used to generate and hash admin passwords.
        storage_service : StorageService
            Service used to upload and remove admin photos.
        email_service : EmailService
            Service used to notify admins of their generated password.
        """
        self.engine = engine
        self.password_service = password_service
        self.storage_service = storage_service
        self.email_service = email_service

    def criar_admin(
        self,
        nome: str,
        email: str,
        periodo: str,
        chapa_id: int,
        foto_bytes: bytes,
        descricao: str,
        linkedin_url: str = "",
        git_url: str = "",
        lattes_url: str = "",
    ) -> Admin:
        """Register a new Admin.

        Generates a random password, hashes it with SHA256 and a salt,
        uploads the admin's photo to the bucket, persists the admin in
        the database, and emails the generated password to the admin.

        Parameters
        ----------
        nome : str
            The admin's name.
        email : str
            The admin's email, used to send the generated password.
        periodo : str
            The academic term.
        chapa_id : int
            The ID of the linked ticket.
        foto_bytes : bytes
            The raw bytes of the admin's photo to upload.
        descricao : str
            The admin's description.
        linkedin_url : str, optional
            The admin's LinkedIn profile URL.
        git_url : str, optional
            The admin's GitHub profile URL.
        lattes_url : str, optional
            The admin's Lattes curriculum URL.

        Returns
        -------
        Admin
            The newly created admin, including its generated id.

        Raises
        ------
        ValueError
            If the email is invalid or already registered, or if the
            given chapa_id does not exist.
        """

    def remover_admin(self, admin_id: int) -> None:
        """Remove an Admin by its identifier.

        Also removes the admin's photo from the bucket.

        Parameters
        ----------
        admin_id : int
            The unique identifier of the admin to remove.

        Raises
        ------
        ValueError
            If no admin with the given id exists.
        """

    def criar_chapa(self, nome: str, ano: int, descricao: str) -> Chapa:
        """Register a new Chapa.

        Parameters
        ----------
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

    def remover_chapa(self, chapa_id: int) -> None:
        """Remove a Chapa by its identifier.

        Parameters
        ----------
        chapa_id : int
            The unique identifier of the ticket to remove.

        Raises
        ------
        ValueError
            If no ticket with the given id exists, or if the ticket
            still has admins linked to it.
        """

    def listar_chapas(self) -> list[Chapa]:
        """Retrieve all registered tickets, for public display.

        Returns
        -------
        list[Chapa]
            A list containing all tickets currently stored, each
            expected to include its associated admins on display.
        """
