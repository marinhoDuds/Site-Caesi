import { describe, it, expect, beforeEach, vi } from 'vitest'

const mockFetch = vi.fn()
global.fetch = mockFetch

async function storeLimpa() {
  localStorage.clear()
  vi.resetModules()
  return import('./auth.ts')
}

describe('stores/auth', () => {
  beforeEach(() => {
    localStorage.clear()
    mockFetch.mockReset()
  })

  it('começa deslogado quando não há nada no localStorage', async () => {
    const { isAdmin, user, mustChangePassword } = await storeLimpa()
    expect(isAdmin.value).toBe(false)
    expect(user.value).toBeNull()
    expect(mustChangePassword.value).toBe(false)
  })

  it('loginAdmin chama endpoint POST /auth/login e salva token no localStorage', async () => {
    const { loginAdmin, isAdmin } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'fake.jwt.token' }),
    })

    const result = await loginAdmin('caesi@ccc.ufcg.edu.br', 'caesi2025')
    expect(result).toBe(true)
    expect(isAdmin.value).toBe(true)
    expect(localStorage.getItem('caesi_admin_token')).toBe('fake.jwt.token')
  })

  it('loginAdmin falha em caso de erro da API', async () => {
    const { loginAdmin, isAdmin } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 })

    const result = await loginAdmin('caesi@ccc.ufcg.edu.br', 'wrong')
    expect(result).toBe(false)
    expect(isAdmin.value).toBe(false)
  })

  it('trocarSenha faz requisição autenticada ao backend', async () => {
    const { loginAdmin, trocarSenha } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'fake.jwt.token' }),
    })
    await loginAdmin('caesi@ccc.ufcg.edu.br', 'caesi2025')

    mockFetch.mockResolvedValueOnce({ ok: true, status: 204 })
    const ok = await trocarSenha('novaSenha123')
    expect(ok).toBe(true)
  })

  it('logout limpa estado e tokens do localStorage', async () => {
    const { loginAdmin, logout, isAdmin } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'fake.jwt.token' }),
    })
    await loginAdmin('caesi@ccc.ufcg.edu.br', 'caesi2025')

    logout()
    expect(isAdmin.value).toBe(false)
    expect(localStorage.getItem('caesi_admin_token')).toBeNull()
  })
})
