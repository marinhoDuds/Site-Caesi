import { ref, computed } from 'vue'
import { upsertEventoFormulario, removeEventoByFormulario } from './calendario.ts'

export type TipoFormulario = 'evento-com-certificado' | 'evento-sem-certificado' | 'venda' | 'arrecadacao'
export type TipoCampo = 'texto' | 'numero' | 'select' | 'checkbox'
export type StatusFormulario = 'aberto' | 'encerrado'
export type StatusComprovante = 'pendente' | 'validado' | 'arquivado'

export interface CampoFormulario {
  id: string
  label: string
  tipo: TipoCampo
  obrigatorio: boolean
  opcoes?: string[]
}

export interface NovoFormulario {
  titulo: string
  tipo: TipoFormulario
  descricao: string
  pago: boolean
  valor: number | null
  prazoInscricao: string | null
  dataEvento: string | null
  limiteVagas: number | null
  requerMatricula: boolean
  campos: CampoFormulario[]
}

export interface Formulario extends NovoFormulario {
  id: number
  status: StatusFormulario
  criadoEm: string
  certificadosEmitidos?: boolean
  certificadosEmitidosEm?: string
}

export interface Comprovante {
  nome: string
  url: string | null
  status: StatusComprovante
}

export interface NovoComprovante {
  nome: string
  url: string | null
}

export interface Cancelamento {
  solicitado: boolean
  motivo: string
  solicitadoEm: string
}

export interface Certificado {
  emitidoEm: string
}

export interface Inscricao {
  id: number
  formularioId: number
  userEmail: string | null
  respostas: Record<string, unknown>
  comprovante: Comprovante | null
  criadoEm: string
  certificado?: Certificado
  cancelamento?: Cancelamento | null
}

export type ResultadoInscricao = { inscricao: Inscricao } | { error: string }
export type ResultadoOperacao = { success: true } | { error: string }

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getHeaders() {
  const token = localStorage.getItem('caesi_admin_token')
  return token ? { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` } : { 'Content-Type': 'application/json' }
}

const _forms = ref<Formulario[]>([])
const _inscricoes = ref<Inscricao[]>([])

export const formularios = computed(() => _forms.value)
export const inscricoes  = computed(() => _inscricoes.value)

export async function fetchFormularios() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/formularios`)
    if (res.ok) {
      const data = await res.json()
      _forms.value = data.map((d: any) => ({ id: d.id, ...JSON.parse(d.content) }))
    }

    const resInsc = await fetch(`${API_BASE}/informations/type/inscricoes`)
    if (resInsc.ok) {
      const data = await resInsc.json()
      _inscricoes.value = data.map((d: any) => ({ id: d.id, ...JSON.parse(d.content) }))
    }
  } catch (error) {
    console.error('Erro ao buscar formulários:', error)
  }
}

export function getFormulario(id: number): Formulario | null {
  return _forms.value.find(f => f.id === id) ?? null
}

export async function addFormulario(dados: NovoFormulario): Promise<Formulario> {
  const tempId = Date.now()
  const novo: Formulario = {
    ...dados,
    id: tempId,
    status: 'aberto',
    criadoEm: new Date().toISOString().split('T')[0],
  }

  try {
    const res = await fetch(`${API_BASE}/admin/informations/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'formularios', content: JSON.stringify(novo) }),
    })
    if (res && res.ok) {
      const data = await res.json()
      if (data && data.id) novo.id = data.id
    }
  } catch (e) {
    console.error(e)
  }

  _forms.value = [..._forms.value, novo]
  upsertEventoFormulario(novo.id, { nome: novo.titulo, data: novo.dataEvento, descricao: novo.descricao })
  return novo
}

export async function updateFormulario(id: number, updates: Partial<Formulario>) {
  const existing = _forms.value.find(f => f.id === id)
  if (!existing) return
  const updated = { ...existing, ...updates }
  _forms.value = _forms.value.map(f => f.id === id ? updated : f)

  try {
    await fetch(`${API_BASE}/admin/informations/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'formularios', content: JSON.stringify(updated) }),
    })
  } catch (e) {
    console.error(e)
  }

  upsertEventoFormulario(id, { nome: updated.titulo, data: updated.dataEvento, descricao: updated.descricao })
}

export async function deleteFormulario(id: number) {
  _forms.value = _forms.value.filter(f => f.id !== id)
  _inscricoes.value = _inscricoes.value.filter(i => i.formularioId !== id)
  removeEventoByFormulario(id)

  try {
    await fetch(`${API_BASE}/admin/informations/${id}`, {
      method: 'DELETE',
      headers: getHeaders(),
    })
  } catch (e) {
    console.error(e)
  }
}

export function getInscricoesByFormulario(formularioId: number): Inscricao[] {
  return _inscricoes.value.filter(i => i.formularioId === formularioId)
}

export async function addInscricao(formularioId: number, respostas: Record<string, unknown>, comprovante: NovoComprovante | null = null): Promise<ResultadoInscricao> {
  const formulario = _forms.value.find(f => f.id === formularioId)
  if (!formulario)                    return { error: 'Formulário não encontrado.' }
  if (formulario.status !== 'aberto') return { error: 'Este formulário está encerrado.' }
  if (formulario.prazoInscricao && new Date(formulario.prazoInscricao + 'T23:59:59') < new Date()) {
    return { error: 'O prazo de inscrição deste formulário já encerrou.' }
  }
  if (formulario.limiteVagas != null) {
    const inscritos = _inscricoes.value.filter(i => i.formularioId === formularioId).length
    if (inscritos >= formulario.limiteVagas) return { error: 'As vagas já foram preenchidas.' }
  }
  const email = (respostas._email as string | undefined)?.trim() || null
  if (email && _inscricoes.value.find(i => i.formularioId === formularioId && i.userEmail === email)) {
    return { error: 'Este e-mail já foi utilizado para se inscrever neste formulário.' }
  }

  const nova: Inscricao = {
    id: Date.now(),
    formularioId,
    userEmail: email,
    respostas,
    comprovante: comprovante ? { ...comprovante, status: 'pendente' } : null,
    criadoEm: new Date().toISOString().split('T')[0],
  }

  try {
    const res = await fetch(`${API_BASE}/informations/public`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ information_type: 'inscricoes', content: JSON.stringify(nova) }),
    })

    if (res && res.ok) {
      const data = await res.json()
      if (data && data.id) nova.id = data.id
    }
  } catch (e) {
    console.error(e)
  }

  _inscricoes.value = [..._inscricoes.value, nova]
  return { inscricao: nova }
}

export async function emitirCertificados(formularioId: number) {
  const hoje = new Date().toISOString().split('T')[0]
  await updateFormulario(formularioId, { certificadosEmitidos: true, certificadosEmitidosEm: hoje })
  _inscricoes.value = _inscricoes.value.map(i =>
    i.formularioId === formularioId ? { ...i, certificado: { emitidoEm: hoje } } : i
  )
}

export async function updateStatusComprovante(inscricaoId: number, status: StatusComprovante) {
  const target = _inscricoes.value.find(i => i.id === inscricaoId)
  if (!target || !target.comprovante) return
  _inscricoes.value = _inscricoes.value.map(i =>
    i.id === inscricaoId && i.comprovante ? { ...i, comprovante: { ...i.comprovante, status } } : i
  )

  try {
    await fetch(`${API_BASE}/admin/informations/${inscricaoId}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'inscricoes', content: JSON.stringify(target) }),
    })
  } catch (e) {
    console.error(e)
  }
}

export async function cancelarInscricaoDireta(inscricaoId: number): Promise<ResultadoOperacao> {
  await fetch(`${API_BASE}/admin/informations/${inscricaoId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  })
  _inscricoes.value = _inscricoes.value.filter(i => i.id !== inscricaoId)
  return { success: true }
}

export async function solicitarCancelamento(inscricaoId: number, motivo = ''): Promise<ResultadoOperacao> {
  const inscricao = _inscricoes.value.find(i => i.id === inscricaoId)
  if (!inscricao) return { error: 'Inscrição não encontrada.' }
  inscricao.cancelamento = { solicitado: true, motivo, solicitadoEm: new Date().toISOString() }

  await fetch(`${API_BASE}/informations/public`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ information_type: 'inscricoes', content: JSON.stringify(inscricao) }),
  })

  return { success: true }
}

export async function aprovarCancelamento(inscricaoId: number): Promise<ResultadoOperacao> {
  return cancelarInscricaoDireta(inscricaoId)
}

export async function recusarCancelamento(inscricaoId: number): Promise<ResultadoOperacao> {
  const inscricao = _inscricoes.value.find(i => i.id === inscricaoId)
  if (!inscricao) return { error: 'Inscrição não encontrada.' }
  inscricao.cancelamento = null

  await fetch(`${API_BASE}/admin/informations/${inscricaoId}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'inscricoes', content: JSON.stringify(inscricao) }),
  })

  return { success: true }
}
