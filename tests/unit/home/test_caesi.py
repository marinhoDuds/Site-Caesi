from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.service.home_management.caesi_service import CaesiService

MODULE = "src.service.home_management.caesi_service"


class TestObterInfo:
    def test_retorna_caesi_quando_encontrado(self):
        row = SimpleNamespace(id=1, nome="CAESI", descricao="Centro Acadêmico...")

        with patch(f"{MODULE}.run_query", return_value=[row]):
            service = CaesiService(MagicMock())
            caesi = service.obter_info()

        assert caesi.id == 1
        assert caesi.nome == "CAESI"
        assert caesi.descricao == "Centro Acadêmico..."

    def test_levanta_erro_quando_nao_ha_registro(self):
        with patch(f"{MODULE}.run_query", return_value=[]):
            service = CaesiService(MagicMock())

            with pytest.raises(ValueError):
                service.obter_info()


class TestAtualizarInfo:
    def test_atualiza_e_retorna_caesi_com_novos_dados(self):
        row_atual = SimpleNamespace(
            id=1, nome="CAESI antigo", descricao="descrição antiga"
        )

        with patch(f"{MODULE}.run_query", side_effect=[[row_atual], 1]):
            service = CaesiService(MagicMock())
            atualizado = service.atualizar_info("CAESI novo", "descrição nova")

        assert atualizado.id == 1
        assert atualizado.nome == "CAESI novo"
        assert atualizado.descricao == "descrição nova"

    def test_levanta_erro_quando_update_nao_afeta_linhas(self):
        row_atual = SimpleNamespace(id=1, nome="CAESI", descricao="descricao")

        with patch(f"{MODULE}.run_query", side_effect=[[row_atual], 0]):
            service = CaesiService(MagicMock())

            with pytest.raises(ValueError):
                service.atualizar_info("Novo nome", "Nova descrição")

    def test_levanta_erro_quando_nao_ha_registro_para_atualizar(self):
        with patch(f"{MODULE}.run_query", return_value=[]):
            service = CaesiService(MagicMock())

            with pytest.raises(ValueError):
                service.atualizar_info("Novo nome", "Nova descrição")
