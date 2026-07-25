import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Publicacao } from './mural.ts'

const mockFetch = vi.fn()
global.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  const mod = await import('./mural.ts')
  return mod
}

describe('stores/mural', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })
  })

  it('addPublicacao, updatePublicacao e deletePublicacao chamam a API', async () => {
    const { addPublicacao, updatePublicacao, deletePublicacao } = await storeLimpa()
    
    // add
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({id: 1, title: 'A'}) }) // add
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, title: 'A'}] }) // fetch
    
    await addPublicacao({ titulo: 'A', tipo: 'Edital', mensagem: 'Mensagem' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/journal/', expect.objectContaining({ method: 'POST' }))

    // update
    mockFetch.mockResolvedValueOnce({ ok: true }) // update
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, title: 'Editado'}] }) // fetch
    
    await updatePublicacao(1, { titulo: 'Editado' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/journal/1', expect.objectContaining({ method: 'PATCH' }))

    // delete
    mockFetch.mockResolvedValueOnce({ ok: true }) // remove
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] }) // fetch
    
    await deletePublicacao(1)
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/journal/1', expect.objectContaining({ method: 'DELETE' }))
  })
})
