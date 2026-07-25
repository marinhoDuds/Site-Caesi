import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8000'

function getHeaders() {
  const token = localStorage.getItem('caesi_admin_token')
  return token ? { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` } : { 'Content-Type': 'application/json' }
}

export interface Anexo {
  nome: string
}

export interface Edital {
  id: number
  titulo: string
  descricao: string
  data: string | null
  anexo: Anexo | null
  criadoEm: string
}

export interface NovoEdital {
  titulo: string
  descricao?: string
  data?: string | null
  anexo?: Anexo | null
}

export interface Professor {
  id: number
  nome: string
  sala: string
  estruturaId: number | null
  descricao: string
  foto: string
  email: string
  lattes: string
  googleAcademico: string
  linkedin: string
}

export interface NovoProfessor {
  nome: string
  sala?: string
  estruturaId?: number | null
  descricao?: string
  foto?: string
  email?: string
  lattes?: string
  googleAcademico?: string
  linkedin?: string
}

export interface Laboratorio {
  id: number
  nome: string
  sigla: string
  descricao: string
  imagem: string | null
  imagens: string[]
  email: string
  linkExterno: string
  estruturaId: number | null
}

export interface NovoLaboratorio {
  nome: string
  sigla?: string
  descricao?: string
  imagem?: string | null
  imagens?: string[]
  email?: string
  linkExterno?: string
  estruturaId?: number | null
}

export interface Tamburetei {
  titulo: string
  descricao: string
  linkExterno: string
}

function hoje(): string { return new Date().toISOString().split('T')[0] }

const _editais = ref<Edital[]>([])
export const editais = computed(() => _editais.value)

export async function fetchEditais() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/announcements`)
    if (!res.ok) throw new Error('Failed to fetch editais')
    const data = await res.json()
    _editais.value = data.map((d: any) => {
      const parsed = JSON.parse(d.content)
      return { id: d.id, ...parsed }
    })
  } catch (error) {
    console.error(error)
  }
}

export async function addEdital(novo: NovoEdital) {
  const content = JSON.stringify({ ...novo, criadoEm: hoje() })
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'announcements', content })
  })
  if (res.ok) {
    const data = await res.json()
    const parsed = JSON.parse(data.content)
    _editais.value.push({ id: data.id, ...parsed })
  }
}

export async function updateEdital(id: number, updates: Partial<Edital>) {
  const existing = _editais.value.find(e => e.id === id)
  if (!existing) return
  const novoConteudo = { ...existing, ...updates }
  delete (novoConteudo as any).id // do not save id in json content
  
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'announcements', content: JSON.stringify(novoConteudo) })
  })
  if (res.ok) {
    const index = _editais.value.findIndex(e => e.id === id)
    if (index !== -1) {
      _editais.value[index] = { id, ...novoConteudo } as Edital
    }
  }
}

export async function deleteEdital(id: number) {
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })
  if (res.ok) {
    _editais.value = _editais.value.filter(e => e.id !== id)
  }
}

const _professores = ref<Professor[]>([])
export const professores = computed(() => _professores.value)

export async function fetchProfessores() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/professors`)
    if (!res.ok) throw new Error('Failed to fetch professores')
    const data = await res.json()
    _professores.value = data.map((d: any) => {
      const parsed = JSON.parse(d.content)
      return { id: d.id, ...parsed }
    })
  } catch (error) {
    console.error(error)
  }
}

export async function addProfessor(novo: NovoProfessor) {
  const content = JSON.stringify(novo)
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'professors', content })
  })
  if (res.ok) {
    const data = await res.json()
    const parsed = JSON.parse(data.content)
    _professores.value.push({ id: data.id, ...parsed })
  }
}

export async function updateProfessor(id: number, updates: Partial<Professor>) {
  const existing = _professores.value.find(p => p.id === id)
  if (!existing) return
  const novoConteudo = { ...existing, ...updates }
  delete (novoConteudo as any).id
  
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'professors', content: JSON.stringify(novoConteudo) })
  })
  if (res.ok) {
    const index = _professores.value.findIndex(p => p.id === id)
    if (index !== -1) {
      _professores.value[index] = { id, ...novoConteudo } as Professor
    }
  }
}

export async function deleteProfessor(id: number) {
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })
  if (res.ok) {
    _professores.value = _professores.value.filter(p => p.id !== id)
  }
}

const _laboratorios = ref<Laboratorio[]>([])
export const laboratorios = computed(() => _laboratorios.value)

export async function fetchLaboratorios() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/laboratories`)
    if (!res.ok) throw new Error('Failed to fetch laboratorios')
    const data = await res.json()
    _laboratorios.value = data.map((d: any) => {
      const parsed = JSON.parse(d.content)
      return { id: d.id, ...parsed }
    })
  } catch (error) {
    console.error(error)
  }
}

export async function addLaboratorio(novo: NovoLaboratorio) {
  const content = JSON.stringify(novo)
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'laboratories', content })
  })
  if (res.ok) {
    const data = await res.json()
    const parsed = JSON.parse(data.content)
    _laboratorios.value.push({ id: data.id, ...parsed })
  }
}

export async function updateLaboratorio(id: number, updates: Partial<Laboratorio>) {
  const existing = _laboratorios.value.find(l => l.id === id)
  if (!existing) return
  const novoConteudo = { ...existing, ...updates }
  delete (novoConteudo as any).id
  
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'laboratories', content: JSON.stringify(novoConteudo) })
  })
  if (res.ok) {
    const index = _laboratorios.value.findIndex(l => l.id === id)
    if (index !== -1) {
      _laboratorios.value[index] = { id, ...novoConteudo } as Laboratorio
    }
  }
}

export async function deleteLaboratorio(id: number) {
  const res = await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })
  if (res.ok) {
    _laboratorios.value = _laboratorios.value.filter(l => l.id !== id)
  }
}

const TAMBURETEI_DEFAULT: Tamburetei = {
  titulo: 'Tamburetei',
  descricao: 'O Tamburetei é uma plataforma colaborativa mantida pela OpenDev UFCG pra ajudar quem tá cursando Ciência da Computação — a ideia é "fazer de tamburete aquela cadeira de CC". Lá você encontra resumos de disciplinas, provas antigas, dicas e materiais compartilhados por outros alunos.\n\nA plataforma está parada há um tempo, mas o repositório continua de pé — e quanto mais gente contribuir, mais viva ela fica. Se você tem provas antigas, resumos ou dicas de alguma disciplina, contribuir é só um pull request de distância.',
  linkExterno: 'https://tamburetei.opendevufcg.org/',
}

const _tamburetei_id = ref<number | null>(null)
const _tamburetei = ref<Tamburetei>({ ...TAMBURETEI_DEFAULT })
export const tamburetei = computed(() => _tamburetei.value)

export async function fetchTamburetei() {
  try {
    const res = await fetch(`${API_BASE}/informations/type/tamburetei`)
    if (!res.ok) throw new Error('Failed to fetch tamburetei')
    const data = await res.json()
    if (data.length > 0) {
      _tamburetei_id.value = data[0].id
      _tamburetei.value = { ...TAMBURETEI_DEFAULT, ...JSON.parse(data[0].content) }
    } else {
      _tamburetei.value = { ...TAMBURETEI_DEFAULT }
    }
  } catch (error) {
    console.error(error)
  }
}

export async function saveTamburetei(dados: Tamburetei) {
  if (_tamburetei_id.value) {
    const res = await fetch(`${API_BASE}/admin/informations/${_tamburetei_id.value}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'tamburetei', content: JSON.stringify(dados) })
    })
    if (res.ok) {
      _tamburetei.value = { ...dados }
    }
  } else {
    const res = await fetch(`${API_BASE}/admin/informations/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'tamburetei', content: JSON.stringify(dados) })
    })
    if (res.ok) {
      const data = await res.json()
      _tamburetei_id.value = data.id
      _tamburetei.value = { ...dados }
    }
  }
}
