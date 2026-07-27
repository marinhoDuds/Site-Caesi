import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8000'

function getHeaders(): Record<string, string> {
  const token = localStorage.getItem('caesi_admin_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export interface Estrutura {
  id: number
  nome: string
  descricao: string
  lat: number
  lng: number
  imagens: string[]
}

export interface NovaEstrutura {
  nome: string
  descricao?: string
  lat: number
  lng: number
  imagens?: string[]
}

const _estruturas = ref<Estrutura[]>([])
export const estruturas = computed(() => _estruturas.value)

export const CENTRO_PADRAO = { lat: -7.2127895, lng: -35.907437 }

export async function fetchEstruturas() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/map`)
    if (!res.ok) throw new Error('Failed to fetch estruturas')
    const data: Array<{ id: number; content: string }> = await res.json()
    _estruturas.value = data.map((d) => {
      const parsed = JSON.parse(d.content)
      return { ...parsed, id: d.id }
    })
  } catch (error) {
    console.error(error)
  }
}

export function getEstrutura(id: number): Estrutura | null {
  return _estruturas.value.find(e => e.id === id) ?? null
}

export async function addEstrutura(nova: NovaEstrutura): Promise<Estrutura | undefined> {
  const content = JSON.stringify(nova)
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'map', content })
  })
  if (res.ok) {
    const data = await res.json()
    const parsed = JSON.parse(data.content)
    const criada: Estrutura = { ...parsed, id: data.id }
    _estruturas.value.push(criada)
    return criada
  }
}

export async function updateEstrutura(id: number, updates: Partial<Estrutura>) {
  const existing = _estruturas.value.find(e => e.id === id)
  if (!existing) return
  const novoConteudo = { ...existing, ...updates }
  delete (novoConteudo as { id?: number }).id
  
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'map', content: JSON.stringify(novoConteudo) })
  })
  if (res.ok) {
    const index = _estruturas.value.findIndex(e => e.id === id)
    if (index !== -1) {
      _estruturas.value[index] = { ...novoConteudo, id } as Estrutura
    }
  }
}

export async function removeEstrutura(id: number) {
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })
  if (res.ok) {
    _estruturas.value = _estruturas.value.filter(e => e.id !== id)
  }
}
