class Caesi:
    """Represents information about CAESI.

    Attributes
    ----------
    id : int
        The unique identifier of CAESI.
    nome : str
        The name of the entity.
    descricao : str
        The description or information about CAESI.
    """

    def __init__(self, id: int, nome: str, descricao: str) -> None:
        """Initialize a new Caesi information object.

        Parameters
        ----------
        id : int
            The unique identifier.
        nome : str
            The name of the entity.
        descricao : str
            The description or history.
        """
        self.id = id
        self.nome = nome
        self.descricao = descricao


class Chapa:
    """Represents an administrative ticket.

    Attributes
    ----------
    id : int
        The unique identifier of the ticket.
    nome : str
        The name of the ticket.
    ano : int
        The effective year of the ticket.
    descricao : str
        The description of proposals or history of the ticket.
    """

    def __init__(self, id: int, nome: str, ano: int, descricao: str) -> None:
        """Initialize a new Chapa.

        Parameters
        ----------
        id : int
            The unique identifier of the ticket.
        nome : str
            The name of the ticket.
        ano : int
            The effective year of the ticket.
        descricao : str
            The description of the ticket.
        """
        self.id = id
        self.nome = nome
        self.ano = ano
        self.descricao = descricao


class Admin:
    """Represents a system administrator associated with a ticket.

    Attributes
    ----------
    id : int
        The unique identifier of the administrator.
    nome : str
        The full name of the administrator.
    email : str
        The email address of the administrator.
    senha_hash : str
        The administrator's password hash.
    salt : str
        The salt used in the password encryption.
    foto_url : str
        The URL of the photo stored in the bucket.
    descricao : str
        A brief description of the administrator.
    periodo : str
        The academic term of the administrator.
    linkedin_url : str, optional
        The LinkedIn profile URL.
    git_url : str, optional
        The GitHub profile URL.
    lattes_url : str, optional
        The Lattes curriculum URL.
    chapa_id : int
        The identifier of the ticket to which the admin belongs.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        email: str,
        senha_hash: str,
        salt: str,
        foto_url: str,
        descricao: str,
        periodo: str,
        chapa_id: int,
        linkedin_url: str = "",
        git_url: str = "",
        lattes_url: str = "",
    ) -> None:
        """Initialize a new Admin.

        Parameters
        ----------
        id : int
            The unique identifier.
        nome : str
            The admin's name.
        email : str
            The admin's email.
        senha_hash : str
            The generated password hash.
        salt : str
            The salt used in the hash.
        foto_url : str
            The URL of the photo in S3.
        descricao : str
            The admin's description.
        periodo : str
            The academic term.
        chapa_id : int
            The ID of the linked ticket.
        linkedin_url : str, optional
            The admin's LinkedIn.
        git_url : str, optional
            The admin's GitHub.
        lattes_url : str, optional
            The admin's Lattes.
        """
        self.id = id
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash
        self.salt = salt
        self.foto_url = foto_url
        self.descricao = descricao
        self.periodo = periodo
        self.linkedin_url = linkedin_url
        self.git_url = git_url
        self.lattes_url = lattes_url
        self.chapa_id = chapa_id