import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8000'

function getHeaders(): Record<string, string> {
  const token = localStorage.getItem('caesi_admin_token')
  return token ? { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` } : { 'Content-Type': 'application/json' }
}

export type PrioridadeTask = 'alta' | 'media' | 'baixa'
export type CategoriaTask = 'gestao' | 'formularios' | 'ouvidoria'
export type StatusTask = 'pendente' | 'em-andamento' | 'concluida'

export interface Anotacao {
  texto: string
  updatedAt: string
}

export interface Task {
  id: string
  titulo: string
  descricao: string
  prioridade: PrioridadeTask
  prazo: string
  categoria: CategoriaTask
  status: StatusTask
  alocados: string[]
  selecionavel: boolean
  criadoEm: string
  anotacoes?: Record<string, Anotacao>
  db_id?: number
}

export interface NovaTask {
  titulo: string
  descricao?: string
  prioridade: PrioridadeTask
  prazo: string
  categoria: CategoriaTask
  alocados?: string[]
  selecionavel?: boolean
}

export interface Membro {
  id: string
  nome: string
  token: string
  db_id?: number
}

interface RegistroArmazenado {
  id: number
  content: string
}

const _tasks = ref<Task[]>([])
const _membros = ref<Membro[]>([])

export const tasks = computed(() => _tasks.value)
export const membros = computed(() => _membros.value)

function parseRegistro<T>(registro: RegistroArmazenado): T & { db_id: number } {
  return { ...JSON.parse(registro.content) as T, db_id: registro.id }
}

export async function fetchTasks() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/tasks`)
    if (res.ok) {
      const data = await res.json()
      _tasks.value = data.map((registro: RegistroArmazenado) => parseRegistro<Task>(registro))
    }
  } catch (error) {
    console.error(error)
  }
}

export async function fetchMembros() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/task_membros`)
    if (res.ok) {
      const data = await res.json()
      _membros.value = data.map((registro: RegistroArmazenado) => parseRegistro<Membro>(registro))
    }
  } catch (error) {
    console.error(error)
  }
}

export async function addMembro(nome: string): Promise<Membro> {
  const membro: Membro = {
    id: crypto.randomUUID(),
    nome: nome.trim(),
    token: crypto.randomUUID(),
  }

  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'task_membros', content: JSON.stringify(membro) })
  })

  if (res.ok) {
    const data = await res.json()
    membro.db_id = data.id
  }

  _membros.value = [..._membros.value, membro]
  return membro
}

export async function removeMembro(id: string) {
  const target = _membros.value.find(m => m.id === id)
  if (target && target.db_id) {
    await fetch(`${API_BASE}/admin/informations/${target.db_id}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
  }

  _membros.value = _membros.value.filter(m => m.id !== id)
  
  const updatedTasks = _tasks.value.map(t => ({
    ...t,
    alocados: t.alocados.filter(a => a !== id),
  }))

  _tasks.value = updatedTasks
  
  for (const t of updatedTasks) {
    if (t.db_id) {
      await fetch(`${API_BASE}/admin/informations/${t.db_id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ information_type: 'tasks', content: JSON.stringify(t) })
      })
    }
  }
}

export function getMembroByToken(token: string): Membro | null {
  return _membros.value.find(m => m.token === token) || null
}

export async function criarTask(dados: NovaTask): Promise<Task> {
  const task: Task = {
    id: crypto.randomUUID(),
    titulo: dados.titulo,
    descricao: dados.descricao || '',
    prioridade: dados.prioridade,
    prazo: dados.prazo,
    categoria: dados.categoria,
    status: 'pendente',
    alocados: dados.alocados || [],
    selecionavel: dados.selecionavel || false,
    criadoEm: new Date().toISOString(),
  }

  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'tasks', content: JSON.stringify(task) })
  })

  if (res.ok) {
    const data = await res.json()
    task.db_id = data.id
  }

  _tasks.value = [..._tasks.value, task]
  return task
}

export async function editarTask(id: string, dados: Partial<Task>) {
  const target = _tasks.value.find(t => t.id === id)
  if (!target) return
  const updated = { ...target, ...dados }

  if (target.db_id) {
    await fetch(`${API_BASE}/admin/informations/${target.db_id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'tasks', content: JSON.stringify(updated) })
    })
  }

  _tasks.value = _tasks.value.map(t => t.id === id ? updated : t)
}

export async function excluirTask(id: string) {
  const target = _tasks.value.find(t => t.id === id)
  if (target && target.db_id) {
    await fetch(`${API_BASE}/admin/informations/${target.db_id}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
  }

  _tasks.value = _tasks.value.filter(t => t.id !== id)
}

export async function atualizarStatus(id: string, status: StatusTask) {
  await editarTask(id, { status })
}

export async function autoAlocar(taskId: string, membroId: string) {
  const target = _tasks.value.find(t => t.id === taskId)
  if (!target || !target.selecionavel || target.alocados.includes(membroId)) return
  await editarTask(taskId, { alocados: [...target.alocados, membroId] })
}

export async function salvarAnotacao(taskId: string, membroId: string, texto: string) {
  const target = _tasks.value.find(t => t.id === taskId)
  if (!target) return
  const anotacoes = { ...(target.anotacoes || {}) }
  if (texto.trim()) {
    anotacoes[membroId] = { texto: texto.trim(), updatedAt: new Date().toISOString() }
  } else {
    delete anotacoes[membroId]
  }
  await editarTask(taskId, { anotacoes })
}
