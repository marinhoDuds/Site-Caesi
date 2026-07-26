import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8000'

function getHeaders() {
  const token = localStorage.getItem('caesi_admin_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

function mapTipoToOperationType(tipo: string): string {
  const map: Record<string, string> = {
    'Ajuda': 'aid',
    'Eventos': 'events',
    'Receita': 'incomes',
    'Infraestrutura': 'infrastructure',
    'Aquisições': 'procurement',
    'Reembolso': 'reimbursement',
    'aid': 'aid',
    'events': 'events',
    'incomes': 'incomes',
    'infrastructure': 'infrastructure',
    'procurement': 'procurement',
    'reimbursement': 'reimbursement',
    'other': 'other'
  }
  return map[tipo] || 'other'
}

export interface Anexo {
  nome: string
}

export interface HistoricoItem {
  data: string
  resumo: string
}

export interface Artefato {
  id: number
  tipo: string
  descricao: string
  valor: number | null
  anexo: Anexo | null
  criadoEm: string
  editadoEm: string | null
  historico: HistoricoItem[]
}

export interface NovoArtefato {
  tipo: string
  descricao: string
  valor?: number | null
  anexo?: Anexo | null
}

const _artefatos = ref<Artefato[]>([])

export const artefatos = computed(() => _artefatos.value)

function hoje(): string {
  return new Date().toISOString().split('T')[0]
}

export function getArtefato(id: number): Artefato | null {
  return _artefatos.value.find(a => a.id === id) ?? null
}

const CAMPOS_LABEL: Record<string, string> = { tipo: 'Tipo', descricao: 'Descrição', valor: 'Valor', anexo: 'Anexo' }

export async function fetchArtefatos() {
  try {
    const res = await fetch(`${API_BASE}/operations`)
    if (res.ok) {
      const data = await res.json()
      _artefatos.value = data.map((op: any) => ({
        id: op.id,
        tipo: op.operation_type,
        descricao: op.description,
        valor: op.value,
        anexo: op.attachment_url ? { nome: op.attachment_url } : null,
        criadoEm: op.created_at || hoje(),
        editadoEm: op.previous ? hoje() : null,
        historico: [{ data: op.created_at || hoje(), resumo: 'Artefato criado' }]
      }))
    }
  } catch (error) {
    console.error(error)
  }
}

export async function addArtefato({ tipo, descricao, valor = null, anexo = null }: NovoArtefato): Promise<Artefato> {
  const formData = new FormData()
  formData.append('value', String(valor ?? 0))
  formData.append('description', descricao)
  formData.append('operation_type', mapTipoToOperationType(tipo))

  let newId = Date.now()
  const res = await fetch(`${API_BASE}/operations`, {
    method: 'POST',
    headers: getHeaders(),
    body: formData
  })

  if (res && res.ok) {
    const data = await res.json()
    newId = data.id
  }

  const novo: Artefato = {
    id: newId,
    tipo,
    descricao,
    valor,
    anexo,
    criadoEm: hoje(),
    editadoEm: null,
    historico: [{ data: hoje(), resumo: 'Artefato criado' }],
  }
  _artefatos.value = [..._artefatos.value, novo]
  return novo
}

export async function updateArtefato(id: number, updates: Partial<Artefato>) {
  const atual = _artefatos.value.find(a => a.id === id)
  if (!atual) return

  const alterados = Object.keys(updates).filter(
    k => CAMPOS_LABEL[k] && JSON.stringify((updates as Record<string, unknown>)[k]) !== JSON.stringify((atual as Record<string, unknown>)[k])
  )
  const novoHistorico = alterados.length
    ? [...atual.historico, { data: hoje(), resumo: `${alterados.map(k => CAMPOS_LABEL[k]).join(', ')} alterado${alterados.length > 1 ? 's' : ''}` }]
    : atual.historico

  const formData = new FormData()
  formData.append('value', String(updates.valor ?? atual.valor ?? 0))
  formData.append('description', updates.descricao ?? atual.descricao)
  formData.append('operation_type', mapTipoToOperationType(updates.tipo ?? atual.tipo))

  await fetch(`${API_BASE}/operations/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: formData
  })

  _artefatos.value = _artefatos.value.map(a => a.id === id
    ? { ...a, ...updates, editadoEm: alterados.length ? hoje() : a.editadoEm, historico: novoHistorico }
    : a
  )
}

export async function deleteArtefato(id: number) {
  try {
    await fetch(`${API_BASE}/operations/${id}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
  } catch (error) {
    console.error('Erro ao deletar artefato:', error)
  }
  _artefatos.value = _artefatos.value.filter(a => a.id !== id)
}
