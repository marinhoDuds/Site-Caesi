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

interface AttachmentBackend {
  id: number
  filename: string
  content_type: string
  url: string
}

interface PublicacaoBackend {
  id: number
  title: string
  post_type: string
  caption: string
  created_at: string
  updated_at: string | null
  attachments?: AttachmentBackend[]
}

type AtualizacaoPublicacao = Pick<PublicacaoBackend, 'title' | 'post_type' | 'caption'>

const _list = ref<Publicacao[]>([])

export const publicacoes = computed(() => _list.value)

function mapBackendToFrontend(post: PublicacaoBackend): Publicacao {
  const attachments = post.attachments || []
  const imagens = attachments
    .filter(a => a.content_type.startsWith('image/'))
    .map(a => a.url.startsWith('http') ? a.url : `${API_BASE}${a.url}`)
  const anexos = attachments
    .filter(a => !a.content_type.startsWith('image/'))
    .map(a => a.url.startsWith('http') ? a.url : `${API_BASE}${a.url}`)

  return {
    id: post.id,
    titulo: post.title,
    tipo: post.post_type,
    mensagem: post.caption,
    imagens,
    anexos,
    criadoEm: new Date(post.created_at).toLocaleDateString('pt-BR'),
    editadoEm: post.updated_at ? new Date(post.updated_at).toLocaleDateString('pt-BR') : null,
  }
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('caesi_admin_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

function extractAttachmentIds(urls: string[] = []): number[] {
  const ids: number[] = []
  for (const u of urls) {
    const match = u.match(/\/attachments\/(\d+)/)
    if (match) {
      ids.push(Number(match[1]))
    }
  }
  return ids
}

async function reassignAttachments(postId: number, urls: string[] = []) {
  const ids = extractAttachmentIds(urls)
  if (!ids.length) return
  try {
    await fetch(`${API_BASE}/admin/attachments/reassign/${postId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(ids),
    })
  } catch (err) {
    console.error('Erro ao reatribuir anexos:', err)
  }
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

export async function addPublicacao(publicacao: NovaPublicacao) {
  const res = await fetch(`${API_BASE}/admin/journal/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify({
      title: publicacao.titulo.trim(),
      post_type: publicacao.tipo.trim(),
      caption: publicacao.mensagem.trim(),
    }),
  })
  if (!res.ok) throw new Error('Erro ao criar publicação')
  
  const created: PublicacaoBackend = await res.json()
  const allUrls = [...(publicacao.imagens || []), ...(publicacao.anexos || [])]
  await reassignAttachments(created.id, allUrls)

  // Fetch updated post with attachments
  const resPost = await fetch(`${API_BASE}/journal/${created.id}`)
  const finalPost = resPost.ok ? await resPost.json() : created

  _list.value = [mapBackendToFrontend(finalPost), ..._list.value]
}

export async function updatePublicacao(id: number, data: Partial<Publicacao>) {
  const payload: Partial<AtualizacaoPublicacao> = {}
  if (data.titulo !== undefined) payload.title = data.titulo
  if (data.tipo !== undefined) payload.post_type = data.tipo
  if (data.mensagem !== undefined) payload.caption = data.mensagem

  const res = await fetch(`${API_BASE}/admin/journal/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Erro ao atualizar publicação')

  const allUrls = [...(data.imagens || []), ...(data.anexos || [])]
  await reassignAttachments(id, allUrls)

  const resPost = await fetch(`${API_BASE}/journal/${id}`)
  const updated = resPost.ok ? await resPost.json() : await res.json()

  _list.value = _list.value.map(post => post.id === id ? mapBackendToFrontend(updated) : post)
}

export async function deletePublicacao(id: number) {
  const res = await fetch(`${API_BASE}/admin/journal/${id}`, {
    method: 'DELETE',
    headers: getAuthHeader(),
  })
  if (!res.ok) throw new Error('Erro ao deletar publicação')
  
  _list.value = _list.value.filter(p => p.id !== id)
}
