import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Artefato } from './portal.ts'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  return import('./portal.ts')
}

describe('stores/portal', () => {
  beforeEach(() => {
    localStorage.clear()
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })
  })

  it('começa vazia quando não há nada no banco/localStorage', async () => {
    const { artefatos } = await storeLimpa()
    expect(artefatos.value).toEqual([])
  })

  it('addArtefato cria com histórico inicial e defaults null', async () => {
    const { artefatos, addArtefato } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 50 }) })

    const novo = await addArtefato({ tipo: 'Ata', descricao: 'Ata de reunião' })

    expect(novo.valor).toBeNull()
    expect(novo.anexo).toBeNull()
    expect(novo.editadoEm).toBeNull()
    expect(novo.historico).toEqual([{ data: novo.criadoEm, resumo: 'Artefato criado' }])
    expect(artefatos.value).toHaveLength(1)
  })

  it('getArtefato encontra pelo id, ou retorna null se não existir', async () => {
    const { addArtefato, getArtefato } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 51 }) })

    const novo = await addArtefato({ tipo: 'Ata', descricao: 'Desc' })

    expect(getArtefato(novo.id)?.tipo).toBe('Ata')
    expect(getArtefato(999999)).toBeNull()
  })

  it('updateArtefato sem mudança real não altera editadoEm nem adiciona histórico', async () => {
    const { artefatos, addArtefato, updateArtefato } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 52 }) })
    const novo = await addArtefato({ tipo: 'Ata', descricao: 'Desc' })

    mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 52 }) })
    await updateArtefato(novo.id, { tipo: 'Ata' }) // mesmo valor de antes

    const atual = artefatos.value.find((a: Artefato) => a.id === novo.id)!
    expect(atual.editadoEm).toBeNull()
    expect(atual.historico).toHaveLength(1)
  })

  it('updateArtefato com mudança real marca editadoEm e adiciona um item no histórico', async () => {
    const { artefatos, addArtefato, updateArtefato } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 53 }) })
    const novo = await addArtefato({ tipo: 'Ata', descricao: 'Desc' })

    mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 53 }) })
    await updateArtefato(novo.id, { tipo: 'Ofício' })

    const atual = artefatos.value.find((a: Artefato) => a.id === novo.id)!
    expect(atual.tipo).toBe('Ofício')
    expect(atual.editadoEm).toBeTypeOf('string')
    expect(atual.historico).toHaveLength(2)
    expect(atual.historico[1].resumo).toBe('Tipo alterado')
  })

  it('updateArtefato com várias mudanças de uma vez junta os rótulos no plural', async () => {
    const { artefatos, addArtefato, updateArtefato } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 54 }) })
    const novo = await addArtefato({ tipo: 'Ata', descricao: 'Desc' })

    mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 54 }) })
    await updateArtefato(novo.id, { tipo: 'Ofício', descricao: 'Nova descrição' })

    const atual = artefatos.value.find((a: Artefato) => a.id === novo.id)!
    expect(atual.historico[1].resumo).toBe('Tipo, Descrição alterados')
  })

  it('updateArtefato ignora campos fora de CAMPOS_LABEL pro histórico', async () => {
    const { artefatos, addArtefato, updateArtefato } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 55 }) })
    const novo = await addArtefato({ tipo: 'Ata', descricao: 'Desc' })

    mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 55 }) })
    await updateArtefato(novo.id, { id: novo.id })

    expect(artefatos.value.find((a: Artefato) => a.id === novo.id)!.historico).toHaveLength(1)
  })

  it('deleteArtefato remove só o artefato indicado', async () => {
    const { artefatos, addArtefato, deleteArtefato } = await storeLimpa()
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 56 }) })
    const a = await addArtefato({ tipo: 'A', descricao: 'Desc A' })

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 57 }) })
    const b = await addArtefato({ tipo: 'B', descricao: 'Desc B' })

    await deleteArtefato(a.id)

    expect(artefatos.value).toHaveLength(1)
    expect(artefatos.value[0].id).toBe(b.id)
  })
})
