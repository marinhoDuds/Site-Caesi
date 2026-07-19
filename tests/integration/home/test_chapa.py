from src.service.home_management.models import Chapa

from .conftest import fake_admin


class TestListarChapasRota:
    def test_inclui_admins_aninhados_sem_campos_sensiveis(
        self, client, mock_admin_service
    ):
        mock_admin_service.listar_chapas.return_value = [
            Chapa(id=1, nome="Chapa A", ano=2026, descricao="desc")
        ]
        mock_admin_service.listar_admins_por_chapa.return_value = [fake_admin()]

        response = client.get("/home/chapa/")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["admins"][0]["email"] == "fulano@example.com"
        assert "senha_hash" not in body[0]["admins"][0]
        assert "salt" not in body[0]["admins"][0]

    def test_retorna_lista_vazia_quando_nao_ha_chapas(self, client, mock_admin_service):
        mock_admin_service.listar_chapas.return_value = []

        response = client.get("/home/chapa/")

        assert response.status_code == 200
        assert response.json() == []


class TestCriarChapaRota:
    def test_retorna_chapa_criada(self, client, mock_admin_service):
        mock_admin_service.criar_chapa.return_value = Chapa(
            id=2, nome="Chapa B", ano=2026, descricao="desc"
        )
        mock_admin_service.listar_admins_por_chapa.return_value = []

        response = client.post(
            "/home/chapa/", params={"nome": "Chapa B", "ano": 2026, "descricao": "desc"}
        )

        assert response.status_code == 200
        assert response.json()["nome"] == "Chapa B"
        assert response.json()["admins"] == []


class TestRemoverChapaRota:
    def test_remove_com_sucesso(self, client, mock_admin_service):
        response = client.delete("/home/chapa/1")

        assert response.status_code == 200
        mock_admin_service.remover_chapa.assert_called_once_with(1)

    def test_retorna_400_quando_ha_admins_vinculados(self, client, mock_admin_service):
        mock_admin_service.remover_chapa.side_effect = ValueError(
            "Chapa 1 still has admins linked to it."
        )

        response = client.delete("/home/chapa/1")

        assert response.status_code == 400
