import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Membro, SecaoCustom } from './equipe.ts'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  return import('./equipe.ts')
}

describe('stores/equipe', () => {
  beforeEach(() => {
    localStorage.clear()
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })
  })

  describe('missão, contato e descrição — valores padrão', () => {
    it('começa com o texto e a imagem padrão da missão quando não há nada salvo', async () => {
      const { missaoTexto, missaoImagem } = await storeLimpa()
      expect(missaoTexto.value).toContain('Centro Acadêmico de Ciência da Computação')
      expect(missaoImagem.value).toBe('')
    })

    it('saveMissao e saveMissaoImagem persistem e refletem no computed', async () => {
      const { missaoTexto, missaoImagem, saveMissao, saveMissaoImagem } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      await saveMissao('Nova missão')
      await saveMissaoImagem('data:image/jpeg;base64,xyz')

      expect(missaoTexto.value).toBe('Nova missão')
      expect(missaoImagem.value).toBe('data:image/jpeg;base64,xyz')
    })

    it('saveMissaoImagem(null) limpa a imagem', async () => {
      const { missaoImagem, saveMissaoImagem } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      await saveMissaoImagem('data:image/jpeg;base64,xyz')
      await saveMissaoImagem(null)
      expect(missaoImagem.value).toBe('')
    })

    it('começa com o contato padrão (endereço/email/instagram do CAESI)', async () => {
      const { contatoInfo } = await storeLimpa()
      expect(contatoInfo.value.email).toBe('caesi@ccc.ufcg.edu.br')
      expect(contatoInfo.value.instagram).toBe('caesiufcg')
    })

    it('saveContato faz merge parcial, sem apagar os outros campos', async () => {
      const { contatoInfo, saveContato } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      await saveContato({ instagram: 'novo_instagram' })

      expect(contatoInfo.value.instagram).toBe('novo_instagram')
      expect(contatoInfo.value.email).toBe('caesi@ccc.ufcg.edu.br')
    })

    it('saveDescricao persiste a descrição da gestão atual', async () => {
      const { descricaoGestao, saveDescricao } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      await saveDescricao('Somos a chapa X')
      expect(descricaoGestao.value).toBe('Somos a chapa X')
    })
  })

  describe('gestaoInfo e periodoFormatado', () => {
    it('periodoFormatado é vazio sem mês/ano de início', async () => {
      const { periodoFormatado } = await storeLimpa()
      expect(periodoFormatado.value).toBe('')
    })

    it('periodoFormatado mostra só o início quando não há fim', async () => {
      const { saveInfo, periodoFormatado } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      await saveInfo({ nomeChapa: 'Chapa X', mesInicio: 'Jan', anoInicio: '2026', mesFim: '', anoFim: '' })
      expect(periodoFormatado.value).toBe('Jan 2026')
    })

    it('periodoFormatado mostra início e fim quando ambos existem', async () => {
      const { saveInfo, periodoFormatado } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      await saveInfo({ nomeChapa: 'Chapa X', mesInicio: 'Jan', anoInicio: '2026', mesFim: 'Dez', anoFim: '2026' })
      expect(periodoFormatado.value).toBe('Jan 2026 – Dez 2026')
    })
  })

  describe('membros', () => {
    it('addMembro gera id e updateMembro/removeMembro afetam só o membro certo', async () => {
      const { membros, addMembro, updateMembro, removeMembro } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 101 }) })
      const a = await addMembro({ nome: 'Ana', email: 'ana@x.com' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 102 }) })
      const b = await addMembro({ nome: 'Bruno', email: 'bruno@x.com' })

      mockFetch.mockResolvedValue({ ok: true })
      await updateMembro(a.id, { diretoria: 'Presidência' })
      expect(membros.value.find((m: Membro) => m.id === a.id)!.diretoria).toBe('Presidência')
      expect(membros.value.find((m: Membro) => m.id === b.id)!.diretoria).toBeUndefined()

      await removeMembro(a.id)
      expect(membros.value).toHaveLength(1)
      expect(membros.value[0].id).toBe(b.id)
    })
  })

  describe('histórico de gestões', () => {
    it('setHistoricoVisivel controla a visibilidade pública, default true', async () => {
      const { historicoVisivel, setHistoricoVisivel } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      expect(historicoVisivel.value).toBe(true)
      await setHistoricoVisivel(false)
      expect(historicoVisivel.value).toBe(false)
    })

    it('adicionarGestaoManual insere no início da lista (mais recente primeiro)', async () => {
      const { historicoGestoes, adicionarGestaoManual } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1 }) })
      await adicionarGestaoManual({ nomeChapa: 'Chapa Antiga', periodo: '2024', descricao: 'Desc' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 2 }) })
      await adicionarGestaoManual({ nomeChapa: 'Chapa Mais Recente', periodo: '2025', descricao: 'Desc' })

      expect(historicoGestoes.value.map(g => g.nomeChapa)).toEqual(['Chapa Mais Recente', 'Chapa Antiga'])
      expect(historicoGestoes.value[0].membros).toEqual([])
    })

    it('arquivarGestaoAtual tira um snapshot da gestão e dos membros atuais', async () => {
      const { historicoGestoes, saveInfo, saveDescricao, addMembro, arquivarGestaoAtual } = await storeLimpa()
      mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })

      await saveInfo({ nomeChapa: 'Chapa Atual', mesInicio: 'Jan', anoInicio: '2026', mesFim: '', anoFim: '' })
      await saveDescricao('Descrição da gestão')
      await addMembro({ nome: 'Ana', email: 'ana@x.com', diretoria: 'Presidência', periodo: '2026.1' })

      await arquivarGestaoAtual()

      expect(historicoGestoes.value).toHaveLength(1)
      const snapshot = historicoGestoes.value[0]
      expect(snapshot.nomeChapa).toBe('Chapa Atual')
      expect(snapshot.periodo).toBe('Jan 2026')
      expect(snapshot.membros).toEqual([{ nome: 'Ana', diretoria: 'Presidência', periodo: '2026.1', foto: '' }])
    })

    it('removerGestaoHistorico remove só a gestão indicada', async () => {
      const { historicoGestoes, adicionarGestaoManual, removerGestaoHistorico } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 201 }) })
      await adicionarGestaoManual({ nomeChapa: 'A', periodo: '2024', descricao: '' })
      const idParaManter = historicoGestoes.value[0].id

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 202 }) })
      await adicionarGestaoManual({ nomeChapa: 'B', periodo: '2025', descricao: '' })
      const idParaRemover = historicoGestoes.value[0].id

      mockFetch.mockResolvedValue({ ok: true })
      await removerGestaoHistorico(idParaRemover)

      expect(historicoGestoes.value).toHaveLength(1)
      expect(historicoGestoes.value[0].id).toBe(idParaManter)
    })
  })

  describe('seções customizadas', () => {
    it('addSecao aplica imagem padrão vazia e updateSecao/removeSecao afetam só a seção certa', async () => {
      const { secoesCustom, addSecao, updateSecao, removeSecao } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 301 }) })
      const a = await addSecao({ titulo: 'A', conteudo: 'Conteúdo A' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 302 }) })
      const b = await addSecao({ titulo: 'B', conteudo: 'Conteúdo B' })

      expect(a.imagem).toBe('')

      mockFetch.mockResolvedValue({ ok: true })
      await updateSecao(a.id, { titulo: 'A editado' })
      expect(secoesCustom.value.find((s: SecaoCustom) => s.id === a.id)!.titulo).toBe('A editado')
      expect(secoesCustom.value.find((s: SecaoCustom) => s.id === b.id)!.titulo).toBe('B')

      await removeSecao(a.id)
      expect(secoesCustom.value).toHaveLength(1)
      expect(secoesCustom.value[0].id).toBe(b.id)
    })

    it('moverSecao troca a posição com a seção vizinha', async () => {
      const { secoesCustom, addSecao, moverSecao } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 301 }) })
      const a = await addSecao({ titulo: 'A', conteudo: '' })
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 302 }) })
      const b = await addSecao({ titulo: 'B', conteudo: '' })
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 303 }) })
      const c = await addSecao({ titulo: 'C', conteudo: '' })

      await moverSecao(b.id, -1) // sobe B: A, B, C -> B, A, C

      expect(secoesCustom.value.map((s: SecaoCustom) => s.id)).toEqual([b.id, a.id, c.id])
    })

    it('moverSecao não faz nada no primeiro item movendo pra cima, nem no último movendo pra baixo', async () => {
      const { secoesCustom, addSecao, moverSecao } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 301 }) })
      const a = await addSecao({ titulo: 'A', conteudo: '' })
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 302 }) })
      const b = await addSecao({ titulo: 'B', conteudo: '' })

      await moverSecao(a.id, -1)
      await moverSecao(b.id, 1)

      expect(secoesCustom.value.map((s: SecaoCustom) => s.id)).toEqual([a.id, b.id])
    })
  })
})
