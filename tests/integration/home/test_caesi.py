from src.service.home_management.models import Caesi


class TestObterInfoCaesiRota:
    def test_retorna_dados_do_caesi(self, client, mock_caesi_service):
        mock_caesi_service.obter_info.return_value = Caesi(
            id=1, nome="CAESI", descricao="desc"
        )

        response = client.get("/home/caesi/")

        assert response.status_code == 200
        assert response.json() == {"id": 1, "nome": "CAESI", "descricao": "desc"}

    def test_retorna_404_quando_nao_ha_informacao_cadastrada(
        self, client, mock_caesi_service
    ):
        mock_caesi_service.obter_info.side_effect = ValueError("not found")

        response = client.get("/home/caesi/")

        assert response.status_code == 404


class TestAtualizarInfoCaesiRota:
    def test_atualiza_e_retorna_dados_novos(self, client, mock_caesi_service):
        mock_caesi_service.atualizar_info.return_value = Caesi(
            id=1, nome="Novo", descricao="Nova desc"
        )

        response = client.put(
            "/home/caesi/", params={"nome": "Novo", "descricao": "Nova desc"}
        )

        assert response.status_code == 200
        mock_caesi_service.atualizar_info.assert_called_once_with("Novo", "Nova desc")

    def test_retorna_400_quando_service_recusa(self, client, mock_caesi_service):
        mock_caesi_service.atualizar_info.side_effect = ValueError("falha ao atualizar")

        response = client.put(
            "/home/caesi/", params={"nome": "Novo", "descricao": "Nova desc"}
        )

        assert response.status_code == 400
