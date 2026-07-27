<script setup lang="ts">
import { computed, onMounted } from 'vue'
import Navbar from '../../components/Navbar.vue'
import BackLink from '../../components/BackLink.vue'
import EmptyState from '../../components/EmptyState.vue'
import MsgCard from '../../components/MsgCard.vue'
import Pagination from '../../components/Pagination.vue'
import { usePagination } from '../../composables/usePagination.ts'
import { usePersistedFilter } from '../../composables/usePersistedFilter.ts'
import { mensagens, fetchMensagens } from '../../stores/mensagens.ts'

onMounted(() => { fetchMensagens() })
import { Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement, Title,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

const filtro = usePersistedFilter('caesi-admin-painel-filtro', 'todas')
const busca  = usePersistedFilter('caesi-admin-painel-busca', '')

const TIPO_LABEL: Record<string, string> = {
  disciplina:     'Disciplina',
  professores:    'Professores',
  colegas:        'Colegas de curso',
  infraestrutura: 'Infraestrutura',
  ofertas:        'Ofertas e horários',
  grupos:         'Grupos estudantis',
  outros:         'Outros',

  classmates:     'Colegas de curso',
  infrastructure: 'Infraestrutura',
  professors:    'Professores',
  schedules:     'Ofertas e horários',
  student_groups: 'Grupos estudantis',
  subjects:       'Disciplina',
  other:          'Outros',
}

const isPendente = (st: string) => {
  const s = (st || '').toLowerCase().trim()
  return s === 'pendente' || s === 'aberto'
}

const isAtendida = (st: string) => {
  const s = (st || '').toLowerCase().trim()
  return s === 'atendida' || s === 'concluido' || s === 'fechado' || s === 'resolvido'
}

const mensagensFiltradas = computed(() => {
  return mensagens.value.filter(m => {
    let matchFiltro = filtro.value === 'todas'
    if (filtro.value === 'pendentes' || filtro.value === 'pendente') {
      matchFiltro = isPendente(m.status)
    } else if (filtro.value === 'atendidas' || filtro.value === 'atendida') {
      matchFiltro = isAtendida(m.status)
    }
    const termo = busca.value.toLowerCase()
    const matchBusca = !termo ||
      (m.preview ?? '').toLowerCase().includes(termo) ||
      (m.nome ?? '').toLowerCase().includes(termo) ||
      (TIPO_LABEL[m.tipo] ?? m.tipo ?? '').toLowerCase().includes(termo)
    return matchFiltro && matchBusca
  })
})

const totalPendente = computed(() => mensagens.value.filter(m => isPendente(m.status)).length)
const totalAtendida = computed(() => mensagens.value.filter(m => isAtendida(m.status)).length)

const { page, totalPages, paginated: mensagensPaginadas, next, prev, goTo } = usePagination(mensagensFiltradas, 15)

function exportarCSV() {
  const cols = ['Protocolo', 'Data', 'Tipo de relato', 'Período', 'Nome', 'E-mail', 'Status', 'Anotação interna']
  const esc = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`
  const linhas = mensagens.value.map(m => [
    m.protocolo,
    m.data,
    TIPO_LABEL[m.tipo] ?? m.tipo ?? '',
    m.periodo ?? '',
    m.nome ?? 'Anônimo',
    m.email ?? '',
    m.status,
    m.nota ?? '',
  ].map(esc).join(','))

  const csv = [cols.map(esc).join(','), ...linhas].join('\r\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `mensagens-caesi-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const TIPO_COR: Record<string, string> = {
  disciplina:     '#4F46E5', // Indigo
  professores:    '#059669', // Emerald Green
  colegas:        '#D97706', // Amber / Warm Gold
  infraestrutura: '#DC2626', // Crimson Red
  ofertas:        '#2563EB', // Royal Blue
  grupos:         '#9333EA', // Purple
  outros:         '#6B7280', // Slate Gray

  subjects:       '#4F46E5', // Indigo
  professors:     '#059669', // Emerald Green
  classmates:     '#D97706', // Amber / Warm Gold
  infrastructure: '#DC2626', // Crimson Red
  schedules:      '#2563EB', // Royal Blue
  student_groups: '#9333EA', // Purple
  other:          '#6B7280', // Slate Gray
}

const donutData = computed(() => {
  const contagem: Record<string, number> = {}
  for (const m of mensagens.value) {
    contagem[m.tipo] = (contagem[m.tipo] ?? 0) + 1
  }
  const tipos = Object.keys(contagem)
  return {
    labels: tipos.map(t => TIPO_LABEL[t] ?? t),
    datasets: [{
      data: tipos.map(t => contagem[t]),
      backgroundColor: tipos.map(t => TIPO_COR[t?.toLowerCase()] ?? '#4F46E5'),
      borderWidth: 2,
      borderColor: '#FEFAF4',
    }],
  }
})

const donutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right' as const, labels: { font: { family: 'Archivo', size: 12 }, padding: 16 } },
  },
}

const barData = computed(() => {
  const meses: Record<string, number> = {}
  const agora = new Date()
  for (let i = 5; i >= 0; i--) {
    const d = new Date(agora.getFullYear(), agora.getMonth() - i, 1)
    const chave = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    meses[chave] = 0
  }
  for (const m of mensagens.value) {
    const d = new Date(m.id)
    const chave = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    if (chave in meses) meses[chave]++
  }
  const labels = Object.keys(meses).map(k => {
    const [ano, mes] = k.split('-')
    return new Date(Number(ano), Number(mes) - 1).toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' })
  })
  return {
    labels,
    datasets: [{
      label: 'Tickets',
      data: Object.values(meses),
      backgroundColor: 'rgba(107,79,187,0.75)',
      borderRadius: 4,
    }],
  }
})

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: { beginAtZero: true, ticks: { stepSize: 1, font: { family: 'Archivo' } }, grid: { color: 'rgba(0,0,0,0.06)' } },
    x: { ticks: { font: { family: 'Archivo' } }, grid: { display: false } },
  },
}
</script>

<template>
  <div class="page">
    <div class="deco-star" style="top:110px;right:2%;font-size:1.2rem;opacity:0.38;">✦</div>
    <div class="deco-star" style="bottom:25%;left:1%;font-size:1.4rem;opacity:0.28;">✦</div>

    <Navbar />

    <div class="page-content">
      <BackLink to="/admin/painel" />
      <div class="page-heading">
        <h2>Painel da <span>Ouvidoria</span></h2>
        <button class="btn btn-outline btn-sm" :disabled="mensagens.length === 0" @click="exportarCSV">
          ↓ Exportar CSV
        </button>
      </div>

      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-number">{{ mensagens.length }}</div>
          <div class="stat-label">Total recebidas</div>
        </div>
        <div class="stat-card stat-card--amarelo">
          <div class="stat-number stat-number--roxo">{{ totalPendente }}</div>
          <div class="stat-label">Pendentes</div>
        </div>
        <div class="stat-card stat-card--verde">
          <div class="stat-number stat-number--verde">{{ totalAtendida }}</div>
          <div class="stat-label">Atendidas</div>
        </div>
      </div>

      <div v-if="mensagens.length > 0" class="charts-grid">
        <div class="paper paper-sm">
          <p class="label-sm" style="margin-bottom:1rem;">Por categoria</p>
          <div class="chart-wrap">
            <Doughnut :data="donutData" :options="donutOptions" />
          </div>
        </div>
        <div class="paper paper-sm">
          <p class="label-sm" style="margin-bottom:1rem;">Tickets por mês</p>
          <div class="chart-wrap">
            <Bar :data="barData" :options="barOptions" />
          </div>
        </div>
      </div>

      <div class="filter-bar">
        <input v-model="busca" type="search" placeholder="Buscar por tipo, nome ou mensagem…">
        <button class="filter-btn" :class="{ active: filtro === 'todas' }"    :aria-pressed="filtro === 'todas'"    @click="filtro = 'todas'">Todas</button>
        <button class="filter-btn" :class="{ active: filtro === 'pendente' }" :aria-pressed="filtro === 'pendente'" @click="filtro = 'pendente'">Pendentes</button>
        <button class="filter-btn" :class="{ active: filtro === 'atendida' }" :aria-pressed="filtro === 'atendida'" @click="filtro = 'atendida'">Atendidas</button>
      </div>

      <MsgCard
        v-for="m in mensagensPaginadas"
        :key="m.id"
        :mensagem="m"
        :to="`/admin/ouvidoria/${m.id}`"
      />

      <EmptyState
        v-if="mensagensFiltradas.length === 0"
        :title="mensagens.length === 0 ? 'Nenhuma mensagem recebida ainda.' : 'Nenhuma mensagem encontrada.'"
        :subtitle="mensagens.length > 0 ? 'Tente outro filtro ou termo de busca.' : undefined"
        style="margin-top:14px;"
      />

      <Pagination :page="page" :totalPages="totalPages" @prev="prev" @next="next" @goto="goTo" />
    </div>
  </div>
</template>

