import io

from .conftest import fake_admin


class TestCriarAdminRota:
    def test_retorna_admin_criado_sem_campos_sensiveis(
        self, client, mock_admin_service
    ):
        mock_admin_service.criar_admin.return_value = fake_admin()

        response = client.post(
            "/home/admin/",
            params={
                "nome": "Fulano",
                "email": "fulano@example.com",
                "periodo": "2026.1",
                "chapa_id": 1,
                "descricao": "desc",
            },
            files={"foto": ("foto.jpg", io.BytesIO(b"fake-bytes"), "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "fulano@example.com"
        assert "senha_hash" not in body
        assert "salt" not in body

    def test_retorna_400_quando_service_recusa(self, client, mock_admin_service):
        mock_admin_service.criar_admin.side_effect = ValueError("email já cadastrado")

        response = client.post(
            "/home/admin/",
            params={
                "nome": "Fulano",
                "email": "fulano@example.com",
                "periodo": "2026.1",
                "chapa_id": 1,
                "descricao": "desc",
            },
            files={"foto": ("foto.jpg", io.BytesIO(b"fake-bytes"), "image/jpeg")},
        )

        assert response.status_code == 400


class TestRemoverAdminRota:
    def test_remove_admin_com_sucesso(self, client, mock_admin_service):
        response = client.delete("/home/admin/1")

        assert response.status_code == 200
        mock_admin_service.remover_admin.assert_called_once_with(1)

    def test_retorna_404_quando_admin_nao_existe(self, client, mock_admin_service):
        mock_admin_service.remover_admin.side_effect = ValueError("not found")

        response = client.delete("/home/admin/999")

        assert response.status_code == 404
