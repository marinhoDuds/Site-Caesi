from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.service.home_management import chapa_service

MODULE = "src.service.home_management.chapa_service"


def _mock_engine_for_insert(lastrowid: int):
    """Build a MagicMock engine so `with engine.connect() as conn` works."""
    result = MagicMock()
    result.lastrowid = lastrowid
    conn = MagicMock()
    conn.execute.return_value = result
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    return engine, conn


class TestCreateChapa:
    def test_retorna_chapa_com_id_gerado(self):
        engine, conn = _mock_engine_for_insert(lastrowid=42)

        chapa = chapa_service.create_chapa(engine, "Chapa Renovação", 2026, "Descrição")

        assert chapa.id == 42
        assert chapa.nome == "Chapa Renovação"
        assert chapa.ano == 2026
        assert chapa.descricao == "Descrição"

    def test_faz_commit_apos_inserir(self):
        engine, conn = _mock_engine_for_insert(lastrowid=1)

        chapa_service.create_chapa(engine, "Chapa X", 2026, "desc")

        conn.commit.assert_called_once()


class TestDeleteChapa:
    def test_remove_chapa_existente(self):
        with patch.object(chapa_service, "run_query", return_value=1) as mock_run:
            chapa_service.delete_chapa(MagicMock(), 5)

        mock_run.assert_called_once()

    def test_levanta_erro_quando_chapa_nao_existe(self):
        with patch.object(chapa_service, "run_query", return_value=0):
            with pytest.raises(ValueError):
                chapa_service.delete_chapa(MagicMock(), 999)


class TestGetAllChapas:
    def test_retorna_lista_de_chapas(self):
        rows = [
            SimpleNamespace(id=1, nome="Chapa A", ano=2025, descricao="desc a"),
            SimpleNamespace(id=2, nome="Chapa B", ano=2026, descricao="desc b"),
        ]

        with patch.object(chapa_service, "run_query", return_value=rows):
            chapas = chapa_service.get_all_chapas(MagicMock())

        assert len(chapas) == 2
        assert chapas[0].nome == "Chapa A"
        assert chapas[1].ano == 2026

    def test_retorna_lista_vazia_quando_nao_ha_chapas(self):
        with patch.object(chapa_service, "run_query", return_value=[]):
            chapas = chapa_service.get_all_chapas(MagicMock())

        assert chapas == []
