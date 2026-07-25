import { ref, computed } from 'vue'

export interface Evento {
  id: number
  nome: string
  data: string
  descricao: string
  formularioId: number | null
}

export interface NovoEvento {
  nome: string
  data: string
  descricao?: string
  formularioId?: number | null
}

export interface DadosEventoFormulario {
  nome: string
  data: string | null | undefined
  descricao: string
}

const _eventos = ref<Evento[]>([])
export const eventos = computed(() => _eventos.value)

function hojeLocalISO(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export const proximosEventos = computed(() => {
  const hoje = hojeLocalISO()
  return _eventos.value
    .filter(e => e.data >= hoje)
    .sort((a, b) => a.data.localeCompare(b.data))
})

const API_URL = 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('token') || ''
}

export async function fetchEventos() {
  try {
    const res = await fetch(`${API_URL}/events/`)
    if (res.ok) {
      const data = await res.json()
      _eventos.value = data.map((e: any) => ({
        id: e.id,
        nome: e.title,
        data: e.scheduled_to,
        descricao: e.description || '',
        formularioId: null // Not supported by backend yet
      }))
    }
  } catch (error) {
    console.error('Erro ao buscar eventos:', error)
  }
}

export function getEvento(id: number): Evento | null {
  return _eventos.value.find(e => e.id === id) ?? null
}

export async function addEvento({ nome, data, descricao = '', formularioId = null }: NovoEvento) {
  try {
    const res = await fetch(`${API_URL}/admin/events/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        title: nome,
        scheduled_to: data,
        description: descricao
      })
    })
    if (res.ok) {
      await fetchEventos()
    } else {
      console.error('Erro ao adicionar evento')
    }
  } catch (error) {
    console.error('Erro ao adicionar evento:', error)
  }
}

export async function updateEvento(id: number, updates: Partial<Evento>) {
  try {
    const event = getEvento(id)
    if (!event) return
    const updated = { ...event, ...updates }
    
    const res = await fetch(`${API_URL}/admin/events/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        title: updated.nome,
        scheduled_to: updated.data,
        description: updated.descricao
      })
    })
    if (res.ok) {
      await fetchEventos()
    } else {
      console.error('Erro ao atualizar evento')
    }
  } catch (error) {
    console.error('Erro ao atualizar evento:', error)
  }
}

export async function removeEvento(id: number) {
  try {
    const res = await fetch(`${API_URL}/admin/events/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    })
    if (res.ok) {
      await fetchEventos()
    } else {
      console.error('Erro ao remover evento')
    }
  } catch (error) {
    console.error('Erro ao remover evento:', error)
  }
}

// These functions will do nothing for now since we removed local storage
export function upsertEventoFormulario(formularioId: number, { nome, data, descricao }: DadosEventoFormulario) {
  console.warn("upsertEventoFormulario not supported with new backend integration yet.")
}

export function removeEventoByFormulario(formularioId: number) {
  console.warn("removeEventoByFormulario not supported with new backend integration yet.")
}
