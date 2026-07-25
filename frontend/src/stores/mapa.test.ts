import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Estrutura } from './mapa.ts'

const mockFetch = vi.fn()
global.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  const mod = await import('./mapa.ts')
  return mod
}

describe('stores/mapa', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })
  })

  it('addEstrutura, updateEstrutura e removeEstrutura chamam a API', async () => {
    const { addEstrutura, updateEstrutura, removeEstrutura, fetchEstruturas } = await storeLimpa()
    
    // add
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"nome":"Bloco CP","lat":-7.21,"lng":-35.9}' }) }) // add
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"nome":"Bloco CP","lat":-7.21,"lng":-35.9}'}] }) // fetch
    
    await addEstrutura({ nome: 'Bloco CP', lat: -7.21, lng: -35.9 })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/', expect.objectContaining({ method: 'POST' }))

    // update
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"nome":"Editado","lat":-7.21,"lng":-35.9}' }) }) // update
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"nome":"Editado","lat":-7.21,"lng":-35.9}'}] }) // fetch
    
    await updateEstrutura(1, { nome: 'Editado' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'PUT' }))

    // remove
    mockFetch.mockResolvedValueOnce({ ok: true }) // remove
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] }) // fetch
    
    await removeEstrutura(1)
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'DELETE' }))
  })
})
