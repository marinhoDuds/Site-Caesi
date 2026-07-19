from pypika import Query, QmarkParameter
from sqlalchemy import Engine, text

from . import chapa_service
from ..database import run_query
from .email_service import EmailService
from .models import Admin, Chapa
from .password_service import PasswordService
from .storage_service import StorageService
from .tables import admin_table, chapa_table


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

    def _insert_and_get_id(self, query) -> int:
        """Execute an INSERT on its own connection and return its new id."""
        param_handler = QmarkParameter()
        sql_query = query.get_sql(parameter=param_handler)
        parameters = param_handler.get_parameters()

        with self.engine.connect() as conn:
            result = conn.execute(text(sql_query), parameters)
            conn.commit()
            return result.lastrowid

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
        if "@" not in email:
            raise ValueError(f"Invalid email: '{email}'.")

        email_query = (
            Query.from_(admin_table)
            .select(admin_table.id)
            .where(admin_table.email == email)
        )
        if run_query(self.engine, email_query):
            raise ValueError(f"Email '{email}' is already registered.")

        chapa_query = (
            Query.from_(chapa_table)
            .select(chapa_table.id)
            .where(chapa_table.id == chapa_id)
        )
        if not run_query(self.engine, chapa_query):
            raise ValueError(f"No chapa found with id {chapa_id}.")

        senha = self.password_service.gerar_senha_aleatoria()
        senha_hash, salt = self.password_service.hash_sha256_salt(senha)

        insert_query = (
            Query.into(admin_table)
            .columns(
                "nome",
                "email",
                "senha_hash",
                "salt",
                "foto_url",
                "descricao",
                "periodo",
                "chapa_id",
                "linkedin_url",
                "git_url",
                "lattes_url",
            )
            .insert(
                nome,
                email,
                senha_hash,
                salt,
                "",
                descricao,
                periodo,
                chapa_id,
                linkedin_url,
                git_url,
                lattes_url,
            )
        )
        admin_id = self._insert_and_get_id(insert_query)

        foto_url = self.storage_service.upload_foto(admin_id, foto_bytes)

        update_query = (
            Query.update(admin_table)
            .set(admin_table.foto_url, foto_url)
            .where(admin_table.id == admin_id)
        )
        run_query(self.engine, update_query)

        self.email_service.enviar_senha(email, senha)

        return Admin(
            id=admin_id,
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            salt=salt,
            foto_url=foto_url,
            descricao=descricao,
            periodo=periodo,
            chapa_id=chapa_id,
            linkedin_url=linkedin_url,
            git_url=git_url,
            lattes_url=lattes_url,
        )

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
        select_query = (
            Query.from_(admin_table)
            .select(admin_table.foto_url)
            .where(admin_table.id == admin_id)
        )
        rows = run_query(self.engine, select_query)

        if not rows:
            raise ValueError(f"No admin found with id {admin_id}.")

        foto_url = rows[0].foto_url

        delete_query = (
            Query.from_(admin_table).where(admin_table.id == admin_id).delete()
        )
        run_query(self.engine, delete_query)

        if foto_url:
            self.storage_service.deletar_foto(foto_url)

    def listar_admins_por_chapa(self, chapa_id: int) -> list[Admin]:
        """Retrieve all admins linked to a given chapa.

        Parameters
        ----------
        chapa_id : int
            The unique identifier of the ticket.

        Returns
        -------
        list[Admin]
            The admins associated with the given chapa.
        """
        query = (
            Query.from_(admin_table)
            .select(
                admin_table.id,
                admin_table.nome,
                admin_table.email,
                admin_table.senha_hash,
                admin_table.salt,
                admin_table.foto_url,
                admin_table.descricao,
                admin_table.periodo,
                admin_table.chapa_id,
                admin_table.linkedin_url,
                admin_table.git_url,
                admin_table.lattes_url,
            )
            .where(admin_table.chapa_id == chapa_id)
        )
        rows = run_query(self.engine, query)

        return [
            Admin(
                id=row.id,
                nome=row.nome,
                email=row.email,
                senha_hash=row.senha_hash,
                salt=row.salt,
                foto_url=row.foto_url,
                descricao=row.descricao,
                periodo=row.periodo,
                chapa_id=row.chapa_id,
                linkedin_url=row.linkedin_url,
                git_url=row.git_url,
                lattes_url=row.lattes_url,
            )
            for row in rows
        ]

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
        return chapa_service.create_chapa(self.engine, nome, ano, descricao)

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
        linked_admins_query = (
            Query.from_(admin_table)
            .select(admin_table.id)
            .where(admin_table.chapa_id == chapa_id)
        )
        if run_query(self.engine, linked_admins_query):
            raise ValueError(f"Chapa {chapa_id} still has admins linked to it.")

        chapa_service.delete_chapa(self.engine, chapa_id)

    def listar_chapas(self) -> list[Chapa]:
        """Retrieve all registered tickets, for public display.

        Returns
        -------
        list[Chapa]
            A list containing all tickets currently stored, each
            expected to include its associated admins on display.
        """
        return chapa_service.get_all_chapas(self.engine)
