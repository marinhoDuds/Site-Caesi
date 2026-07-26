import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8000'

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
  _admin.value ? { role: 'admin', nome: 'Admin', email: 'admin' } : null
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

    localStorage.setItem('caesi_admin', '1')
    localStorage.setItem('caesi_admin_token', token)
    _admin.value = true
    return true
  } catch {
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
}
