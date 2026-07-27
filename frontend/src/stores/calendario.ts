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
  return localStorage.getItem('caesi_admin_token') || ''
}

export async function fetchEventos() {
  try {
    const res = await fetch(`${API_URL}/events/`)
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data)) {
        _eventos.value = data.map((e: { id: number; title: string; scheduled_to: string; description?: string; formulario_id?: number | null }) => ({
          id: e.id,
          nome: e.title,
          data: e.scheduled_to,
          descricao: e.description || '',
          formularioId: e.formulario_id ?? null
        }))
      }
    }
  } catch (error) {
    console.error('Erro ao buscar eventos:', error)
  }
}

export function getEvento(id: number): Evento | null {
  return _eventos.value.find(e => e.id === id) ?? null
}

export async function addEvento({ nome, data, descricao = '', formularioId = null }: NovoEvento) {
  const tempId = Date.now()
  const novoEvento: Evento = {
    id: tempId,
    nome,
    data,
    descricao,
    formularioId
  }
  const existingIdx = _eventos.value.findIndex(e => e.id === tempId || (formularioId !== null && e.formularioId === formularioId))
  if (existingIdx === -1) {
    _eventos.value.push(novoEvento)
  }

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
        description: descricao,
        formulario_id: formularioId
      })
    })
    if (res.ok) {
      if (typeof res.json === 'function') {
        const created = await res.json()
        if (created && created.id) {
          const idx = _eventos.value.findIndex(e => e.id === tempId || (formularioId !== null && e.formularioId === formularioId))
          if (idx !== -1) {
            _eventos.value[idx].id = created.id
          }
        }
      }
    } else {
      console.error('Erro ao adicionar evento')
    }
  } catch (error) {
    console.error('Erro ao adicionar evento:', error)
  }
}

export async function updateEvento(id: number, updates: Partial<Evento>) {
  const idx = _eventos.value.findIndex(e => e.id === id)
  if (idx !== -1) {
    _eventos.value[idx] = { ..._eventos.value[idx], ...updates }
  }
  const updated = getEvento(id) || ({ id, nome: '', data: '', descricao: '', formularioId: null, ...updates } as Evento)

  try {
    const res = await fetch(`${API_URL}/admin/events/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        title: updated.nome,
        scheduled_to: updated.data,
        description: updated.descricao,
        formulario_id: updated.formularioId
      })
    })
    if (!res.ok) {
      console.error('Erro ao atualizar evento')
    }
  } catch (error) {
    console.error('Erro ao atualizar evento:', error)
  }
}

export async function removeEvento(id: number) {
  _eventos.value = _eventos.value.filter(e => e.id !== id)
  try {
    const res = await fetch(`${API_URL}/admin/events/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    })
    if (!res.ok) {
      console.error('Erro ao remover evento')
    }
  } catch (error) {
    console.error('Erro ao remover evento:', error)
  }
}

export function upsertEventoFormulario(formularioId: number, { nome, data, descricao }: DadosEventoFormulario) {
  const existing = _eventos.value.find(e => e.formularioId === formularioId)

  if (!data) {
    if (existing) {
      removeEvento(existing.id)
    }
    return
  }

  if (existing) {
    updateEvento(existing.id, {
      nome,
      data,
      descricao: descricao || '',
      formularioId
    })
  } else {
    addEvento({
      nome,
      data,
      descricao: descricao || '',
      formularioId
    })
  }
}

export function removeEventoByFormulario(formularioId: number) {
  const existing = _eventos.value.find(e => e.formularioId === formularioId)
  if (existing) {
    removeEvento(existing.id)
  }
}

function escapeIcsText(str: string): string {
  return (str || '')
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\r\n/g, '\n')
    .replace(/\n/g, '\\n')
}

function buildIcsEventBlock(e: Evento): string {
  const cleanDate = e.data.split('T')[0].replace(/-/g, '')
  const uid = `evento-${e.id}@caesi.ufcg`
  const dtstamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
  return [
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${dtstamp}`,
    `DTSTART;VALUE=DATE:${cleanDate}`,
    `SUMMARY:${escapeIcsText(e.nome)}`,
    `DESCRIPTION:${escapeIcsText(e.descricao)}`,
    'END:VEVENT'
  ].join('\r\n')
}

export function exportarEventoIcs(evento: Evento) {
  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//CAESI UFCG//Calendario//PT-BR',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    buildIcsEventBlock(evento),
    'END:VCALENDAR'
  ].join('\r\n')

  const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${evento.nome.toLowerCase().replace(/\s+/g, '-')}.ics`
  a.click()
  URL.revokeObjectURL(url)
}

export function exportarTodosEventosIcs(listaEventos: Evento[] = _eventos.value) {
  if (listaEventos.length === 0) return
  const vevents = listaEventos.map(buildIcsEventBlock).join('\r\n')
  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//CAESI UFCG//Calendario Completo//PT-BR',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    vevents,
    'END:VCALENDAR'
  ].join('\r\n')

  const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'caesi-agenda-completa.ics'
  a.click()
  URL.revokeObjectURL(url)
}
