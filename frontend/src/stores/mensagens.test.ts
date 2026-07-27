import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Mensagem } from './mensagens.ts'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  return import('./mensagens.ts')
}

const ticketApiResponse = {
  id: 1,
  protocol: 'PROT-001',
  ticket_type: 'infrastructure',
  semester: '2026.1',
  content: 'Descrição do problema com tamanho suficiente para o preview.',
  author: 'Maria',
  email: 'maria@ufcg.edu.br',
  status: 'pendente',
  admin_notes: null,
  updated_at: null,
}

describe('stores/mensagens', () => {
  beforeEach(() => {
    localStorage.clear()
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({ ok: true, json: async () => [] })
  })

  it('começa vazia antes do fetch', async () => {
    const { mensagens } = await storeLimpa()
    expect(mensagens.value).toEqual([])
  })

  it('fetchMensagens popula a lista com dados da API', async () => {
    const { mensagens, fetchMensagens } = await storeLimpa()

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [ticketApiResponse],
    })

    await fetchMensagens()

    expect(mensagens.value).toHaveLength(1)
    expect(mensagens.value[0].protocolo).toBe('PROT-001')
    expect(mensagens.value[0].tipo).toBe('infrastructure')
    expect(mensagens.value[0].status).toBe('pendente')
  })

  it('fetchMensagens mapeia o preview truncado corretamente', async () => {
    const { mensagens, fetchMensagens } = await storeLimpa()
    const corpoLongo = 'x'.repeat(150)

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [{ ...ticketApiResponse, content: corpoLongo }],
    })

    await fetchMensagens()

    expect(mensagens.value[0].preview).toBe('x'.repeat(110) + '…')
  })

  it('fetchMensagens não quebra em caso de erro de rede', async () => {
    const { mensagens, fetchMensagens } = await storeLimpa()

    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    await fetchMensagens()

    expect(mensagens.value).toEqual([])
  })

  it('updateStatus chama PATCH e atualiza localmente', async () => {
    const { mensagens, fetchMensagens, updateStatus } = await storeLimpa()

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [ticketApiResponse] })
    await fetchMensagens()

    mockFetch.mockResolvedValueOnce({ ok: true })
    await updateStatus(1, 'atendida')

    expect(mensagens.value.find((m: Mensagem) => m.id === 1)!.status).toBe('atendida')
    const patchCall = mockFetch.mock.calls.find(call => String(call[0]).includes('PROT-001'))
    expect(patchCall).toBeDefined()
    expect(JSON.parse(patchCall![1].body)).toMatchObject({ status: 'atendida' })
  })

  it('updateNota chama PATCH e atualiza localmente', async () => {
    const { mensagens, fetchMensagens, updateNota } = await storeLimpa()

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [ticketApiResponse] })
    await fetchMensagens()

    mockFetch.mockResolvedValueOnce({ ok: true })
    await updateNota(1, 'Encaminhado à coordenação.')

    expect(mensagens.value.find((m: Mensagem) => m.id === 1)!.nota).toBe('Encaminhado à coordenação.')
  })

  it('deleteMensagem remove a mensagem localmente', async () => {
    const { mensagens, fetchMensagens, deleteMensagem } = await storeLimpa()

    const segundo = { ...ticketApiResponse, id: 2, protocol: 'PROT-002' }
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [ticketApiResponse, segundo] })
    await fetchMensagens()

    await deleteMensagem(1)

    expect(mensagens.value).toHaveLength(1)
    expect(mensagens.value[0].id).toBe(2)
  })
})
