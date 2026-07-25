import { ref } from 'vue'

const CHAVE_CONQUISTA_SECRETA = 'caesi_conquista_secreta'

export const conquistaSecretaDesbloqueada = ref(localStorage.getItem(CHAVE_CONQUISTA_SECRETA) === 'true')

export function marcarConquistaSecreta(): boolean {
  if (conquistaSecretaDesbloqueada.value) return false
  conquistaSecretaDesbloqueada.value = true
  localStorage.setItem(CHAVE_CONQUISTA_SECRETA, 'true')
  return true
}
