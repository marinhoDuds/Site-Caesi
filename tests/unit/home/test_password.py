from src.service.crypto import hash_password
from src.service.home_management.password_service import PasswordService


class TestGerarSenhaAleatoria:
    def test_tamanho_padrao(self):
        service = PasswordService()

        senha = service.gerar_senha_aleatoria()

        assert len(senha) == 12

    def test_tamanho_customizado(self):
        service = PasswordService()

        senha = service.gerar_senha_aleatoria(20)

        assert len(senha) == 20

    def test_senhas_geradas_sao_diferentes(self):
        service = PasswordService()

        senha1 = service.gerar_senha_aleatoria()
        senha2 = service.gerar_senha_aleatoria()

        assert senha1 != senha2


class TestHashSha256Salt:
    def test_retorna_hash_e_salt_como_strings(self):
        service = PasswordService()

        senha_hash, salt = service.hash_sha256_salt("minha_senha")

        assert isinstance(senha_hash, str)
        assert isinstance(salt, str)

    def test_hash_nao_e_a_senha_em_texto_puro(self):
        service = PasswordService()

        senha_hash, _ = service.hash_sha256_salt("minha_senha")

        assert senha_hash != "minha_senha"

    def test_hash_bate_com_verificacao_manual_usando_o_salt_gerado(self):
        service = PasswordService()

        senha_hash, salt = service.hash_sha256_salt("minha_senha")

        assert hash_password("minha_senha", salt) == senha_hash

    def test_cada_chamada_gera_salt_e_hash_diferentes(self):
        service = PasswordService()

        senha_hash1, salt1 = service.hash_sha256_salt("minha_senha")
        senha_hash2, salt2 = service.hash_sha256_salt("minha_senha")

        assert salt1 != salt2
        assert senha_hash1 != senha_hash2
