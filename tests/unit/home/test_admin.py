from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.service.home_management import admin_service as admin_service_module
from src.service.home_management.admin_service import AdminService

MODULE = "src.service.home_management.admin_service"


def _mock_engine_for_insert(lastrowid: int):
    """Build a MagicMock engine so `with engine.connect() as conn` works."""
    result = MagicMock()
    result.lastrowid = lastrowid
    conn = MagicMock()
    conn.execute.return_value = result
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    return engine, conn


def _make_collaborators():
    password_service = MagicMock()
    password_service.gerar_senha_aleatoria.return_value = "senha-gerada"
    password_service.hash_sha256_salt.return_value = ("hash123", "salt123")

    storage_service = MagicMock()
    storage_service.upload_foto.return_value = "http://s3.local/admins/10.jpg"

    email_service = MagicMock()

    return password_service, storage_service, email_service


class TestCriarAdmin:
    def test_caminho_feliz_cria_admin_e_notifica(self):
        password_service, storage_service, email_service = _make_collaborators()
        engine, conn = _mock_engine_for_insert(lastrowid=10)
        service = AdminService(engine, password_service, storage_service, email_service)

        # 1a chamada: email já cadastrado? -> não
        # 2a chamada: chapa existe? -> sim
        # 3a chamada: update do foto_url
        with patch.object(
            admin_service_module,
            "run_query",
            side_effect=[[], [SimpleNamespace(id=1)], 1],
        ):
            admin = service.criar_admin(
                nome="Fulano",
                email="fulano@example.com",
                periodo="2026.1",
                chapa_id=1,
                foto_bytes=b"foto",
                descricao="descricao",
            )

        assert admin.id == 10
        assert admin.email == "fulano@example.com"
        assert admin.senha_hash == "hash123"
        assert admin.salt == "salt123"
        assert admin.foto_url == "http://s3.local/admins/10.jpg"
        storage_service.upload_foto.assert_called_once_with(10, b"foto")
        email_service.enviar_senha.assert_called_once_with(
            "fulano@example.com", "senha-gerada"
        )

    def test_levanta_erro_com_email_invalido(self):
        password_service, storage_service, email_service = _make_collaborators()
        service = AdminService(
            MagicMock(), password_service, storage_service, email_service
        )

        with pytest.raises(ValueError):
            service.criar_admin(
                nome="Fulano",
                email="email-invalido",
                periodo="2026.1",
                chapa_id=1,
                foto_bytes=b"foto",
                descricao="descricao",
            )

    def test_levanta_erro_quando_email_ja_cadastrado(self):
        password_service, storage_service, email_service = _make_collaborators()
        service = AdminService(
            MagicMock(), password_service, storage_service, email_service
        )

        with patch.object(
            admin_service_module, "run_query", side_effect=[[SimpleNamespace(id=1)]]
        ):
            with pytest.raises(ValueError):
                service.criar_admin(
                    nome="Fulano",
                    email="ja@existe.com",
                    periodo="2026.1",
                    chapa_id=1,
                    foto_bytes=b"foto",
                    descricao="descricao",
                )

    def test_levanta_erro_quando_chapa_nao_existe(self):
        password_service, storage_service, email_service = _make_collaborators()
        service = AdminService(
            MagicMock(), password_service, storage_service, email_service
        )

        with patch.object(admin_service_module, "run_query", side_effect=[[], []]):
            with pytest.raises(ValueError):
                service.criar_admin(
                    nome="Fulano",
                    email="novo@example.com",
                    periodo="2026.1",
                    chapa_id=999,
                    foto_bytes=b"foto",
                    descricao="descricao",
                )

    def test_nao_envia_email_quando_criacao_falha_por_chapa_invalida(self):
        password_service, storage_service, email_service = _make_collaborators()
        service = AdminService(
            MagicMock(), password_service, storage_service, email_service
        )

        with patch.object(admin_service_module, "run_query", side_effect=[[], []]):
            with pytest.raises(ValueError):
                service.criar_admin(
                    nome="Fulano",
                    email="novo@example.com",
                    periodo="2026.1",
                    chapa_id=999,
                    foto_bytes=b"foto",
                    descricao="descricao",
                )

        email_service.enviar_senha.assert_not_called()
        storage_service.upload_foto.assert_not_called()


class TestRemoverAdmin:
    def test_remove_admin_e_apaga_foto(self):
        storage_service = MagicMock()
        service = AdminService(MagicMock(), MagicMock(), storage_service, MagicMock())

        with patch.object(
            admin_service_module,
            "run_query",
            side_effect=[[SimpleNamespace(foto_url="http://s3.local/admins/1.jpg")], 1],
        ):
            service.remover_admin(1)

        storage_service.deletar_foto.assert_called_once_with(
            "http://s3.local/admins/1.jpg"
        )

    def test_levanta_erro_quando_admin_nao_existe(self):
        service = AdminService(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        with patch.object(admin_service_module, "run_query", side_effect=[[]]):
            with pytest.raises(ValueError):
                service.remover_admin(999)

    def test_nao_apaga_foto_quando_admin_nao_possui_uma(self):
        storage_service = MagicMock()
        service = AdminService(MagicMock(), MagicMock(), storage_service, MagicMock())

        with patch.object(
            admin_service_module,
            "run_query",
            side_effect=[[SimpleNamespace(foto_url="")], 1],
        ):
            service.remover_admin(1)

        storage_service.deletar_foto.assert_not_called()


class TestListarAdminsPorChapa:
    def test_retorna_admins_da_chapa(self):
        service = AdminService(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        row = SimpleNamespace(
            id=1,
            nome="Fulano",
            email="fulano@example.com",
            senha_hash="h",
            salt="s",
            foto_url="url",
            descricao="d",
            periodo="2026.1",
            chapa_id=5,
            linkedin_url="",
            git_url="",
            lattes_url="",
        )

        with patch.object(admin_service_module, "run_query", return_value=[row]):
            admins = service.listar_admins_por_chapa(5)

        assert len(admins) == 1
        assert admins[0].nome == "Fulano"
        assert admins[0].chapa_id == 5


class TestDelegacaoParaChapaService:
    def test_criar_chapa_delega_para_chapa_service(self):
        service = AdminService(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        fake_chapa = MagicMock()

        with patch.object(
            admin_service_module.chapa_service, "create_chapa", return_value=fake_chapa
        ) as mock_create:
            resultado = service.criar_chapa("Chapa X", 2026, "desc")

        mock_create.assert_called_once_with(service.engine, "Chapa X", 2026, "desc")
        assert resultado is fake_chapa

    def test_remover_chapa_levanta_erro_se_ha_admins_vinculados(self):
        service = AdminService(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        with patch.object(
            admin_service_module, "run_query", return_value=[SimpleNamespace(id=1)]
        ):
            with pytest.raises(ValueError):
                service.remover_chapa(5)

    def test_remover_chapa_delega_quando_nao_ha_admins_vinculados(self):
        service = AdminService(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        with patch.object(admin_service_module, "run_query", return_value=[]):
            with patch.object(
                admin_service_module.chapa_service, "delete_chapa"
            ) as mock_delete:
                service.remover_chapa(5)

        mock_delete.assert_called_once_with(service.engine, 5)

    def test_listar_chapas_delega_para_chapa_service(self):
        service = AdminService(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        fake_chapas = [MagicMock(), MagicMock()]

        with patch.object(
            admin_service_module.chapa_service,
            "get_all_chapas",
            return_value=fake_chapas,
        ) as mock_get_all:
            resultado = service.listar_chapas()

        mock_get_all.assert_called_once_with(service.engine)
        assert resultado == fake_chapas
