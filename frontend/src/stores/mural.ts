import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8000'

export interface Publicacao {
  id: number
  titulo: string
  tipo: string
  mensagem: string
  imagens: string[]
  anexos: string[]
  criadoEm: string
  editadoEm: string | null
}

export interface NovaPublicacao {
  titulo: string
  tipo: string
  mensagem: string
  imagens?: string[]
  anexos?: string[]
}

const _list = ref<Publicacao[]>([])

export const publicacoes = computed(() => _list.value)

// Mapper: Backend PostResponse -> Frontend Publicacao
function mapBackendToFrontend(post: any): Publicacao {
  return {
    id: post.id,
    titulo: post.title,
    tipo: post.post_type,
    mensagem: post.caption,
    imagens: [],
    anexos: [],
    criadoEm: new Date(post.created_at).toLocaleDateString('pt-BR'),
    editadoEm: post.updated_at ? new Date(post.updated_at).toLocaleDateString('pt-BR') : null,
  }
}

function getAuthHeader() {
  const token = localStorage.getItem('caesi_admin_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

export async function fetchPublicacoes() {
  try {
    const res = await fetch(`${API_BASE}/journal/`)
    if (!res.ok) throw new Error('Erro ao buscar publicações')
    const data = await res.json()
    _list.value = data.map(mapBackendToFrontend)
  } catch (error) {
    console.error(error)
  }
}

export async function addPublicacao({ titulo, tipo, mensagem, imagens, anexos }: NovaPublicacao) {
  const res = await fetch(`${API_BASE}/admin/journal/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify({
      title: titulo.trim(),
      post_type: tipo.trim(),
      caption: mensagem.trim()
    })
  })
  if (!res.ok) throw new Error('Erro ao criar publicação')
  
  const created = await res.json()
  _list.value = [mapBackendToFrontend(created), ..._list.value]
}

export async function updatePublicacao(id: number, data: Partial<Publicacao>) {
  const payload: any = {}
  if (data.titulo !== undefined) payload.title = data.titulo
  if (data.tipo !== undefined) payload.post_type = data.tipo
  if (data.mensagem !== undefined) payload.caption = data.mensagem

  const res = await fetch(`${API_BASE}/admin/journal/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error('Erro ao atualizar publicação')

  const updated = await res.json()
  _list.value = _list.value.map(p => p.id === id ? mapBackendToFrontend(updated) : p)
}

export async function deletePublicacao(id: number) {
  const res = await fetch(`${API_BASE}/admin/journal/${id}`, {
    method: 'DELETE',
    headers: getAuthHeader()
  })
  if (!res.ok) throw new Error('Erro ao deletar publicação')
  
  _list.value = _list.value.filter(p => p.id !== id)
}
