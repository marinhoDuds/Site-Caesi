import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Task } from './tasks.ts'

const mockFetch = vi.fn()
global.fetch = mockFetch

async function storeLimpa() {
  vi.resetModules()
  return import('./tasks.ts')
}

describe('stores/tasks', () => {
  beforeEach(() => {
    localStorage.clear()
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })
  })

  describe('membros', () => {
    it('começa vazia e addMembro cria com id/token únicos', async () => {
      const { membros, addMembro } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1 }) })

      const m = await addMembro('  Ana  ')

      expect(membros.value).toHaveLength(1)
      expect(m.nome).toBe('Ana')
      expect(m.id).toBeTypeOf('string')
      expect(m.token).toBeTypeOf('string')
      expect(m.id).not.toBe(m.token)
    })

    it('getMembroByToken encontra pelo token, ou retorna null', async () => {
      const { addMembro, getMembroByToken } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 2 }) })

      const m = await addMembro('Ana')

      expect(getMembroByToken(m.token)?.nome).toBe('Ana')
      expect(getMembroByToken('token-invalido')).toBeNull()
    })

    it('removeMembro remove o membro e desaloca ele de todas as tasks', async () => {
      const { tasks, membros, addMembro, criarTask, removeMembro } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 10 }) })
      const ana = await addMembro('Ana')

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 11 }) })
      const bruno = await addMembro('Bruno')

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 100 }) })
      const task = await criarTask({ titulo: 'Task', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao', alocados: [ana.id, bruno.id] })

      mockFetch.mockResolvedValue({ ok: true })
      await removeMembro(ana.id)

      expect(membros.value).toHaveLength(1)
      expect(membros.value[0].id).toBe(bruno.id)
      const atual = tasks.value.find((t: Task) => t.id === task.id)!
      expect(atual.alocados).toEqual([bruno.id])
    })
  })

  describe('tasks', () => {
    it('criarTask aplica defaults (descricao, alocados, selecionavel, status)', async () => {
      const { tasks, criarTask } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 200 }) })

      const task = await criarTask({ titulo: 'Nova task', prioridade: 'alta', prazo: '2026-08-01', categoria: 'ouvidoria' })

      expect(task.descricao).toBe('')
      expect(task.alocados).toEqual([])
      expect(task.selecionavel).toBe(false)
      expect(task.status).toBe('pendente')
      expect(tasks.value).toHaveLength(1)
    })

    it('editarTask atualiza só os campos informados, na task certa', async () => {
      const { tasks, criarTask, editarTask } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 201 }) })
      const a = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 202 }) })
      const b = await criarTask({ titulo: 'B', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValue({ ok: true })
      await editarTask(a.id, { titulo: 'A editado' })

      expect(tasks.value.find((t: Task) => t.id === a.id)!.titulo).toBe('A editado')
      expect(tasks.value.find((t: Task) => t.id === b.id)!.titulo).toBe('B')
    })

    it('excluirTask remove só a task indicada', async () => {
      const { tasks, criarTask, excluirTask } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 203 }) })
      const a = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 204 }) })
      const b = await criarTask({ titulo: 'B', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValue({ ok: true })
      await excluirTask(a.id)

      expect(tasks.value).toHaveLength(1)
      expect(tasks.value[0].id).toBe(b.id)
    })

    it('atualizarStatus muda só o status da task indicada', async () => {
      const { tasks, criarTask, atualizarStatus } = await storeLimpa()
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 205 }) })

      const task = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValue({ ok: true })
      await atualizarStatus(task.id, 'em-andamento')

      expect(tasks.value.find((t: Task) => t.id === task.id)!.status).toBe('em-andamento')
    })
  })

  describe('autoAlocar', () => {
    it('adiciona o membro aos alocados quando a task é selecionável', async () => {
      const { tasks, criarTask, addMembro, autoAlocar } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 301 }) })
      const task = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao', selecionavel: true })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 302 }) })
      const membro = await addMembro('Ana')

      mockFetch.mockResolvedValue({ ok: true })
      await autoAlocar(task.id, membro.id)

      expect(tasks.value.find((t: Task) => t.id === task.id)!.alocados).toEqual([membro.id])
    })

    it('não faz nada quando a task não é selecionável', async () => {
      const { tasks, criarTask, addMembro, autoAlocar } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 303 }) })
      const task = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao', selecionavel: false })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 304 }) })
      const membro = await addMembro('Ana')

      await autoAlocar(task.id, membro.id)

      expect(tasks.value.find((t: Task) => t.id === task.id)!.alocados).toEqual([])
    })

    it('não duplica o membro se ele já estiver alocado', async () => {
      const { tasks, criarTask, addMembro, autoAlocar } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 305 }) })
      const membro = await addMembro('Ana')

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 306 }) })
      const task = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao', selecionavel: true, alocados: [membro.id] })

      await autoAlocar(task.id, membro.id)

      expect(tasks.value.find((t: Task) => t.id === task.id)!.alocados).toEqual([membro.id])
    })
  })

  describe('salvarAnotacao', () => {
    it('cria uma anotação nova pro membro', async () => {
      const { tasks, criarTask, addMembro, salvarAnotacao } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 401 }) })
      const task = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 402 }) })
      const membro = await addMembro('Ana')

      mockFetch.mockResolvedValue({ ok: true })
      await salvarAnotacao(task.id, membro.id, 'Minha anotação')

      const atual = tasks.value.find((t: Task) => t.id === task.id)!
      expect(atual.anotacoes?.[membro.id].texto).toBe('Minha anotação')
    })

    it('remove a anotação quando o texto fica vazio', async () => {
      const { tasks, criarTask, addMembro, salvarAnotacao } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 403 }) })
      const task = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 404 }) })
      const membro = await addMembro('Ana')

      mockFetch.mockResolvedValue({ ok: true })
      await salvarAnotacao(task.id, membro.id, 'Texto')
      await salvarAnotacao(task.id, membro.id, '   ')

      const atual = tasks.value.find((t: Task) => t.id === task.id)!
      expect(atual.anotacoes?.[membro.id]).toBeUndefined()
    })

    it('anotações de membros diferentes na mesma task não se sobrescrevem', async () => {
      const { tasks, criarTask, addMembro, salvarAnotacao } = await storeLimpa()

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 405 }) })
      const task = await criarTask({ titulo: 'A', prioridade: 'media', prazo: '2026-08-01', categoria: 'gestao' })

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 406 }) })
      const ana = await addMembro('Ana')

      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 407 }) })
      const bruno = await addMembro('Bruno')

      mockFetch.mockResolvedValue({ ok: true })
      await salvarAnotacao(task.id, ana.id, 'Anotação da Ana')
      await salvarAnotacao(task.id, bruno.id, 'Anotação do Bruno')

      const atual = tasks.value.find((t: Task) => t.id === task.id)!
      expect(atual.anotacoes?.[ana.id].texto).toBe('Anotação da Ana')
      expect(atual.anotacoes?.[bruno.id].texto).toBe('Anotação do Bruno')
    })
  })
})
