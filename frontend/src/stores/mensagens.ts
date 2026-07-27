import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8000'

function getAdminHeaders(): Record<string, string> {
  const token = localStorage.getItem('caesi_admin_token')
  return token
    ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
    : { 'Content-Type': 'application/json' }
}

export type StatusMensagem = 'pendente' | 'atendida'

export interface Complemento {
  texto: string
  data: string
}

export interface NovaMensagem {
  tipo: string
  periodo: string
  corpo: string
  nome: string | null
  email: string | null
}

export interface Mensagem extends NovaMensagem {
  id: number
  protocolo: string
  status: StatusMensagem
  nota: string
  data: string
  preview: string
  complementos?: Complemento[]
}

function normalizeStatus(st: unknown): StatusMensagem {
  const str = String(st || '').toLowerCase().trim()
  if (str === 'atendida' || str === 'concluida' || str === 'fechado' || str === 'resolvido') {
    return 'atendida'
  }
  return 'pendente'
}

function mapTicketToMensagem(t: Record<string, unknown>): Mensagem {
  const corpo = String(t.content ?? '')
  return {
    id: Number(t.id),
    protocolo: String(t.protocol ?? ''),
    tipo: String(t.ticket_type ?? ''),
    periodo: String(t.semester ?? ''),
    corpo,
    nome: t.author ? String(t.author) : null,
    email: t.email ? String(t.email) : null,
    status: normalizeStatus(t.status),
    nota: String(t.admin_notes ?? ''),
    data: t.updated_at ? String(t.updated_at) : new Date().toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }),
    preview: corpo.slice(0, 110) + (corpo.length > 110 ? '…' : ''),
  }
}

const _list = ref<Mensagem[]>([])

export const mensagens = computed(() => _list.value)

export async function fetchMensagens() {
  try {
    const res = await fetch(`${API_BASE}/admin/tickets/`, { headers: getAdminHeaders() })
    if (res.ok) {
      const data: Record<string, unknown>[] = await res.json()
      _list.value = data.map(mapTicketToMensagem)
    }
  } catch (error) {
    console.error('Erro ao buscar tickets:', error)
  }
}

export async function updateStatus(id: number, status: StatusMensagem) {
  const mensagem = _list.value.find(m => m.id === id)
  if (!mensagem) return
  try {
    await fetch(`${API_BASE}/admin/tickets/${mensagem.protocolo}`, {
      method: 'PATCH',
      headers: getAdminHeaders(),
      body: JSON.stringify({ status }),
    })
  } catch (error) {
    console.error('Erro ao atualizar status:', error)
  }
  _list.value = _list.value.map(m => m.id === id ? { ...m, status } : m)
}

export async function updateNota(id: number, nota: string) {
  const mensagem = _list.value.find(m => m.id === id)
  if (!mensagem) return
  try {
    await fetch(`${API_BASE}/admin/tickets/${mensagem.protocolo}`, {
      method: 'PATCH',
      headers: getAdminHeaders(),
      body: JSON.stringify({ admin_notes: nota }),
    })
  } catch (error) {
    console.error('Erro ao salvar nota:', error)
  }
  _list.value = _list.value.map(m => m.id === id ? { ...m, nota } : m)
}

export async function deleteMensagem(id: number) {
  _list.value = _list.value.filter(m => m.id !== id)
}
