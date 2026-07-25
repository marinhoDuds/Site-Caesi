import { describe, it, expect, beforeEach, vi } from 'vitest'

const mockFetch = vi.fn()
global.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  const mod = await import('./informacoes.ts')
  return mod
}

describe('stores/informacoes', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })
  })

  it('addEdital, updateEdital e deleteEdital chamam a API', async () => {
    const { addEdital, updateEdital, deleteEdital } = await storeLimpa()
    
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"titulo":"Edital 1"}' }) })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"titulo":"Edital 1"}'}] })
    await addEdital({ titulo: 'Edital 1' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/', expect.objectContaining({ method: 'POST' }))

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"titulo":"Editado"}' }) })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"titulo":"Editado"}'}] })
    await updateEdital(1, { titulo: 'Editado' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'PUT' }))

    mockFetch.mockResolvedValueOnce({ ok: true })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] })
    await deleteEdital(1)
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('addProfessor, updateProfessor e deleteProfessor chamam a API', async () => {
    const { addProfessor, updateProfessor, deleteProfessor } = await storeLimpa()
    
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"nome":"A"}' }) })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"nome":"A"}'}] })
    await addProfessor({ nome: 'A' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/', expect.objectContaining({ method: 'POST' }))

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"nome":"A","sala":"Sala 101"}' }) })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"nome":"A","sala":"Sala 101"}'}] })
    await updateProfessor(1, { sala: 'Sala 101' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'PUT' }))

    mockFetch.mockResolvedValueOnce({ ok: true })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] })
    await deleteProfessor(1)
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('addLaboratorio, updateLaboratorio e deleteLaboratorio chamam a API', async () => {
    const { addLaboratorio, updateLaboratorio, deleteLaboratorio } = await storeLimpa()
    
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"nome":"LSD"}' }) })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"nome":"LSD"}'}] })
    await addLaboratorio({ nome: 'LSD' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/', expect.objectContaining({ method: 'POST' }))

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, content: '{"nome":"LSD","sigla":"AAA"}' }) })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"nome":"LSD","sigla":"AAA"}'}] })
    await updateLaboratorio(1, { sigla: 'AAA' })
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'PUT' }))

    mockFetch.mockResolvedValueOnce({ ok: true })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] })
    await deleteLaboratorio(1)
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('saveTamburetei chama a API para atualizar as informações do Tamburetei', async () => {
    const { saveTamburetei } = await storeLimpa()
    
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({id: 1, content: '{"titulo":"Novo"}'}) })
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{id: 1, content: '{"titulo":"Novo"}'}] })
    
    await saveTamburetei({ titulo: 'Novo' } as any)
    
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/admin/informations/', expect.objectContaining({ method: 'POST' }))
  })
})
