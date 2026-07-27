import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import type { Evento } from './calendario.ts'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  const mod = await import('./calendario.ts')
  return mod
}

describe('stores/calendario', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-15T12:00:00'))
  })
  afterEach(() => { vi.useRealTimers() })

  it('proximosEventos inclui hoje e o futuro, exclui o passado, ordenado por data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, title: 'Passado', scheduled_to: '2026-06-01', description: '' },
        { id: 2, title: 'Hoje', scheduled_to: '2026-06-15', description: '' },
        { id: 3, title: 'Futuro distante', scheduled_to: '2026-08-01', description: '' },
        { id: 4, title: 'Futuro próximo', scheduled_to: '2026-07-01', description: '' }
      ]
    })
    
    const { fetchEventos, proximosEventos } = await storeLimpa()
    await fetchEventos()

    expect(proximosEventos.value.map((e: Evento) => e.nome)).toEqual([
      'Hoje', 'Futuro próximo', 'Futuro distante',
    ])
  })

  it('getEvento encontra pelo id', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, title: 'Prova', scheduled_to: '2026-07-01', description: '' }
      ]
    })
    
    const { fetchEventos, getEvento } = await storeLimpa()
    await fetchEventos()

    expect(getEvento(1)?.nome).toBe('Prova')
    expect(getEvento(999999)).toBeNull()
  })

  it('addEvento, updateEvento e removeEvento chamam a API', async () => {
    const { addEvento, updateEvento, removeEvento } = await storeLimpa()
    
    mockFetch.mockResolvedValueOnce({ ok: true }) // add
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, title: 'A', scheduled_to: '2026-07-01', description: ''}] }) // fetch
    
    await addEvento({ nome: 'A', data: '2026-07-01' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/events/', expect.objectContaining({ method: 'POST' }))

    mockFetch.mockResolvedValueOnce({ ok: true }) // update
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, title: 'A editado', scheduled_to: '2026-07-01', description: ''}] }) // fetch
    
    await updateEvento(1, { nome: 'A editado' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/events/1', expect.objectContaining({ method: 'PUT' }))

    mockFetch.mockResolvedValueOnce({ ok: true }) // remove
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] }) // fetch
    
    await removeEvento(1)
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/events/1', expect.objectContaining({ method: 'DELETE' }))
  })
})
