import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface AuthUser {
  role: 'admin'
  nome: string
  email: string
}

const _admin = ref(!!localStorage.getItem('caesi_admin'))

export const isAdmin = computed(() => _admin.value)
export const isLoggedIn = computed(() => _admin.value)
export const mustChangePassword = computed(() => false)
export const user = computed<AuthUser | null>(() =>
  _admin.value ? { role: 'admin', nome: 'Admin', email: 'admin@caesi.ufcg.edu.br' } : null
)

export async function loginAdmin(email: string, senha: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim().toLowerCase(), password: senha }),
    })

    if (!res.ok) return false

    const data = await res.json()
    const token: string = data.access_token
    const refreshToken: string = data.refresh_token || ''

    localStorage.setItem('caesi_admin', '1')
    localStorage.setItem('caesi_admin_token', token)
    if (refreshToken) {
      localStorage.setItem('caesi_refresh_token', refreshToken)
    }
    _admin.value = true
    return true
  } catch {
    return false
  }
}

export async function renovarToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem('caesi_refresh_token')
  if (!refreshToken) return false

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!res.ok) {
      logout()
      return false
    }

    const data = await res.json()
    if (data.access_token) {
      localStorage.setItem('caesi_admin_token', data.access_token)
      if (data.refresh_token) {
        localStorage.setItem('caesi_refresh_token', data.refresh_token)
      }
      return true
    }
    return false
  } catch {
    logout()
    return false
  }
}

export function loginComGoogle() {
  _admin.value = true
  localStorage.setItem('caesi_admin', '1')
}

export async function trocarSenha(novaSenha: string): Promise<boolean> {
  const token = localStorage.getItem('caesi_admin_token')
  if (!token) return false

  try {
    const res = await fetch(`${API_BASE}/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ new_password: novaSenha }),
    })
    return res.ok || res.status === 204
  } catch {
    return false
  }
}

export function logout() {
  _admin.value = false
  localStorage.removeItem('caesi_admin')
  localStorage.removeItem('caesi_admin_token')
  localStorage.removeItem('caesi_refresh_token')
}
