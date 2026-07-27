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

export interface Membro {
  id: number
  nome: string
  email: string
  diretoria?: string
  periodo?: string
  foto?: string
  descricao?: string
  linkedin?: string
  git?: string
  lattes?: string
}

export type NovoMembro = Omit<Membro, 'id'>

export interface GestaoInfo {
  nomeChapa: string
  mesInicio: string
  anoInicio: string
  mesFim: string
  anoFim: string
}

export interface MembroHistorico {
  nome: string
  diretoria: string
  periodo: string
  foto: string
}

export interface GestaoHistorico {
  id: number
  nomeChapa: string
  periodo: string
  descricao: string
  membros: MembroHistorico[]
}

export interface NovaGestaoManual {
  nomeChapa: string
  periodo: string
  descricao: string
  membros?: MembroHistorico[]
}

export interface ContatoInfo {
  endereco: string
  email: string
  instagram: string
}

export interface SecaoCustom {
  id: number
  titulo: string
  conteudo: string
  imagem: string
}

export interface NovaSecaoCustom {
  titulo: string
  conteudo: string
  imagem?: string
}

const MISSAO_DEFAULT = `O CAESI, Centro Acadêmico de Ciência da Computação, é a entidade estudantil
que representa os alunos do curso de Ciência da Computação da UFCG. Nossa missão é defender
os direitos e interesses dos estudantes, promover a integração acadêmica e facilitar a comunicação
entre o corpo discente e a instituição.

A ouvidoria é um dos nossos canais mais importantes: um espaço para que qualquer aluno possa
relatar problemas, sugerir melhorias ou entrar em contato com o CAESI de forma segura, inclusive anônima.`

const CONTATO_DEFAULT: ContatoInfo = {
  endereco:  'Sala do CAESI — Bloco CP, UFCG, Campina Grande – PB',
  email:     'caesi@ccc.ufcg.edu.br',
  instagram: 'caesiufcg',
}

const INFO_DEFAULT: GestaoInfo = { nomeChapa: '', mesInicio: '', anoInicio: '', mesFim: '', anoFim: '' }

const _membros = ref<Membro[]>([])
const _descricao = ref<string>('')
const _info = ref<GestaoInfo>({ ...INFO_DEFAULT })
const _historico = ref<GestaoHistorico[]>([])
const _histVis = ref<boolean>(true)
const _missao = ref<string>(MISSAO_DEFAULT)
const _missaoImg = ref<string>('')
const _contato = ref<ContatoInfo>({ ...CONTATO_DEFAULT })
const _secoes = ref<SecaoCustom[]>([])

const _gestao_info_id = ref<number | null>(null)
const _missao_id = ref<number | null>(null)
const _contato_id = ref<number | null>(null)

const MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

export const membros            = computed(() => _membros.value)
export const descricaoGestao    = computed(() => _descricao.value)
export const gestaoInfo         = computed(() => _info.value)
export const historicoGestoes   = computed(() => _historico.value)
export const historicoVisivel   = computed(() => _histVis.value)
export const missaoTexto        = computed(() => _missao.value)
export const missaoImagem       = computed(() => _missaoImg.value)
export const contatoInfo        = computed(() => _contato.value)
export const secoesCustom       = computed(() => _secoes.value)
export const periodoFormatado  = computed(() => {
  const { mesInicio, anoInicio, mesFim, anoFim } = _info.value
  if (!mesInicio || !anoInicio) return ''
  const fim = mesFim && anoFim ? ` – ${mesFim} ${anoFim}` : ''
  return `${mesInicio} ${anoInicio}${fim}`
})
export { MESES }

export async function fetchEquipe() {
  try {
    const resMembros = await fetch(`${API_BASE}/informations/type/membros`)
    if (resMembros.ok) {
      const data = await resMembros.json()
      _membros.value = data.map((d: { id: number; content: string }) => ({ id: d.id, ...JSON.parse(d.content) }))
    }

    const resGestao = await fetch(`${API_BASE}/informations/type/gestao_info`)
    if (resGestao.ok) {
      const data = await resGestao.json()
      if (data.length > 0) {
        _gestao_info_id.value = data[0].id
        const parsed = JSON.parse(data[0].content)
        _descricao.value = parsed.descricao ?? ''
        _info.value = { ...INFO_DEFAULT, ...(parsed.info || {}) }
        _histVis.value = parsed.histVis ?? true
      }
    }

    const resHist = await fetch(`${API_BASE}/informations/type/gestoes_anteriores`)
    if (resHist.ok) {
      const data = await resHist.json()
      _historico.value = data.map((d: { id: number; content: string }) => ({ id: d.id, ...JSON.parse(d.content) }))
    }

    const resMissao = await fetch(`${API_BASE}/informations/type/sobre_missao`)
    if (resMissao.ok) {
      const data = await resMissao.json()
      if (data.length > 0) {
        _missao_id.value = data[0].id
        const parsed = JSON.parse(data[0].content)
        _missao.value = parsed.texto ?? MISSAO_DEFAULT
        _missaoImg.value = parsed.imagem ?? ''
      }
    }

    const resContato = await fetch(`${API_BASE}/informations/type/sobre_contato`)
    if (resContato.ok) {
      const data = await resContato.json()
      if (data.length > 0) {
        _contato_id.value = data[0].id
        _contato.value = { ...CONTATO_DEFAULT, ...JSON.parse(data[0].content) }
      }
    }

    const resSecoes = await fetch(`${API_BASE}/informations/type/sobre_secoes`)
    if (resSecoes.ok) {
      const data = await resSecoes.json()
      _secoes.value = data.map((d: { id: number; content: string }) => ({ id: d.id, ...JSON.parse(d.content) }))
    }
  } catch (error) {
    console.error(error)
  }
}

async function persistGestaoInfo() {
  const payload = {
    descricao: _descricao.value,
    info: _info.value,
    histVis: _histVis.value
  }
  const content = JSON.stringify(payload)
  if (_gestao_info_id.value) {
    await fetch(`${API_BASE}/admin/informations/${_gestao_info_id.value}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'gestao_info', content })
    })
  } else {
    const res = await fetch(`${API_BASE}/admin/informations/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'gestao_info', content })
    })
    if (res && res.ok) {
      const data = await res.json()
      _gestao_info_id.value = data.id
    }
  }
}

async function persistMissao() {
  const content = JSON.stringify({ texto: _missao.value, imagem: _missaoImg.value })
  if (_missao_id.value) {
    await fetch(`${API_BASE}/admin/informations/${_missao_id.value}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'sobre_missao', content })
    })
  } else {
    const res = await fetch(`${API_BASE}/admin/informations/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'sobre_missao', content })
    })
    if (res && res.ok) {
      const data = await res.json()
      _missao_id.value = data.id
    }
  }
}

async function persistContato() {
  const content = JSON.stringify(_contato.value)
  if (_contato_id.value) {
    await fetch(`${API_BASE}/admin/informations/${_contato_id.value}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'sobre_contato', content })
    })
  } else {
    const res = await fetch(`${API_BASE}/admin/informations/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ information_type: 'sobre_contato', content })
    })
    if (res && res.ok) {
      const data = await res.json()
      _contato_id.value = data.id
    }
  }
}

export async function addMembro(membro: NovoMembro): Promise<Membro> {
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'membros', content: JSON.stringify(membro) })
  })
  let newId = Date.now()
  if (res && res.ok) {
    const data = await res.json()
    newId = data.id
  }
  const novo: Membro = { ...membro, id: newId }
  _membros.value = [..._membros.value, novo]
  return novo
}

export async function removeMembro(id: number) {
  await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })
  _membros.value = _membros.value.filter(a => a.id !== id)
}

export async function updateMembro(id: number, data: Partial<Membro>) {
  const existing = _membros.value.find(a => a.id === id)
  if (!existing) return
  const updated = { ...existing, ...data }
  const payload = { ...updated }
  delete (payload as { id?: number }).id

  await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'membros', content: JSON.stringify(payload) })
  })
  _membros.value = _membros.value.map(a => a.id === id ? updated : a)
}

export async function saveMissao(texto: string) {
  _missao.value = texto
  await persistMissao()
}

export async function saveMissaoImagem(dataUrl: string | null) {
  _missaoImg.value = dataUrl || ''
  await persistMissao()
}

export async function saveContato(dados: Partial<ContatoInfo>) {
  _contato.value = { ..._contato.value, ...dados }
  await persistContato()
}

export async function saveDescricao(texto: string) {
  _descricao.value = texto
  await persistGestaoInfo()
}

export async function saveInfo(info: GestaoInfo) {
  _info.value = { ...info }
  await persistGestaoInfo()
}

export async function setHistoricoVisivel(val: boolean) {
  _histVis.value = val
  await persistGestaoInfo()
}

export async function adicionarGestaoManual({ nomeChapa, periodo, descricao, membros }: NovaGestaoManual) {
  const contentObj = { nomeChapa, periodo, descricao, membros: membros ?? [] }
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'gestoes_anteriores', content: JSON.stringify(contentObj) })
  })
  let newId = Date.now()
  if (res && res.ok) {
    const data = await res.json()
    newId = data.id
  }
  const entrada: GestaoHistorico = { id: newId, ...contentObj }
  _historico.value = [entrada, ..._historico.value]
}

export async function arquivarGestaoAtual() {
  const contentObj = {
    nomeChapa: _info.value.nomeChapa,
    periodo:  periodoFormatado.value,
    descricao: _descricao.value,
    membros:  _membros.value.map(({ nome, diretoria, periodo, foto }) => ({ nome, diretoria: diretoria ?? '', periodo: periodo ?? '', foto: foto ?? '' })),
  }
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'gestoes_anteriores', content: JSON.stringify(contentObj) })
  })
  let newId = Date.now()
  if (res && res.ok) {
    const data = await res.json()
    newId = data.id
  }
  const entrada: GestaoHistorico = { id: newId, ...contentObj }
  _historico.value = [entrada, ..._historico.value]
}

export async function removerGestaoHistorico(id: number) {
  await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })
  _historico.value = _historico.value.filter(g => g.id !== id)
}

export async function addSecao({ titulo, conteudo, imagem = '' }: NovaSecaoCustom): Promise<SecaoCustom> {
  const payload = { titulo, conteudo, imagem }
  const res = await fetch(`${API_BASE}/admin/informations/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'sobre_secoes', content: JSON.stringify(payload) })
  })
  let newId = Date.now()
  if (res && res.ok) {
    const data = await res.json()
    newId = data.id
  }
  const nova: SecaoCustom = { id: newId, titulo, conteudo, imagem }
  _secoes.value = [..._secoes.value, nova]
  return nova
}

export async function updateSecao(id: number, data: Partial<SecaoCustom>) {
  const existing = _secoes.value.find(s => s.id === id)
  if (!existing) return
  const updated = { ...existing, ...data }
  const payload = { ...updated }
  delete (payload as { id?: number }).id

  await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({ information_type: 'sobre_secoes', content: JSON.stringify(payload) })
  })
  _secoes.value = _secoes.value.map(s => s.id === id ? updated : s)
}

export async function removeSecao(id: number) {
  await fetch(`${API_BASE}/admin/informations/${id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })
  _secoes.value = _secoes.value.filter(s => s.id !== id)
}

export async function moverSecao(id: number, direcao: number) {
  const list = [..._secoes.value]
  const idx = list.findIndex(s => s.id === id)
  const alvo = idx + direcao
  if (idx < 0 || alvo < 0 || alvo >= list.length) return
  ;[list[idx], list[alvo]] = [list[alvo], list[idx]]
  _secoes.value = list
}
