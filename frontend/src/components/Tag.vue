<script setup lang="ts">
defineProps<{
  tipo: string
}>()

const classMap: Record<string, string> = {
  disciplina:     'tag-disciplina',
  professores:    'tag-professores',
  colegas:        'tag-colegas',
  infraestrutura: 'tag-infraestrutura',
  ofertas:        'tag-ofertas',
  grupos:         'tag-grupos',
  outros:         'tag-outros',

  classmates:     'tag-colegas',
  infrastructure: 'tag-infraestrutura',
  professors:    'tag-professores',
  schedules:     'tag-ofertas',
  student_groups: 'tag-grupos',
  subjects:       'tag-disciplina',
  other:          'tag-outros',
}

const labelMap: Record<string, string> = {
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
</script>

<template>
  <span class="tag" :class="classMap[(tipo || '').toLowerCase()] ?? 'tag-outros'">
    {{ labelMap[(tipo || '').toLowerCase()] ?? tipo }}
  </span>
</template>
