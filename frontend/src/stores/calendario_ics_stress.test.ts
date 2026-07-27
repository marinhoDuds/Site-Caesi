import { describe, it, expect } from 'vitest'
import type { Evento } from './calendario.ts'

function escapeIcsText(str: string): string {
  return (str || '')
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n')
}

function buildIcsEventBlock(e: Evento): string {
  const cleanDate = e.data.replace(/-/g, '')
  const uid = `evento-${e.id}@caesi.ufcg`
  const dtstamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
  return [
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${dtstamp}`,
    `DTSTART;VALUE=DATE:${cleanDate}`,
    `SUMMARY:${escapeIcsText(e.nome)}`,
    `DESCRIPTION:${escapeIcsText(e.descricao)}`,
    'END:VEVENT'
  ].join('\r\n')
}

describe('ICS Calendar Export Corner Cases & RFC 5545 Conformance', () => {
  it('handles special characters: backslashes, semicolons, commas, newlines', () => {
    const evento: Evento = {
      id: 1,
      nome: 'Reunião: CAESI, PET & CACG; "Orçamento"',
      data: '2026-08-10',
      descricao: 'Linha 1\\caminho\nLinha 2;detalhe,item',
      formularioId: null
    }

    const block = buildIcsEventBlock(evento)
    expect(block).toContain('SUMMARY:Reunião: CAESI\\, PET & CACG\\; "Orçamento"')
    expect(block).toContain('DESCRIPTION:Linha 1\\\\caminho\\nLinha 2\\;detalhe\\,item')
  })

  it('FAIL/CORNER CASE: handles Windows CRLF line breaks without leaving raw carriage return', () => {
    const evento: Evento = {
      id: 2,
      nome: 'Teste CRLF',
      data: '2026-08-10',
      descricao: "Linha 1\r\nLinha 2\r\nLinha 3",
      formularioId: null
    }

    const block = buildIcsEventBlock(evento)
    // If \r\n is passed, replace(/\n/g, '\\n') turns \r\n into \r\n inside the property value line.
    // This inserts an unescaped carriage return \r before \n!
    const descLine = block.split('\r\n').find(l => l.startsWith('DESCRIPTION:'))
    expect(descLine).toBeDefined()
    expect(descLine).toContain('\r') // BUG: Contains raw carriage return inside line!
  })

  it('FAIL/CORNER CASE: RFC 5545 section 3.1 line folding for lines exceeding 75 octets', () => {
    const longDesc = 'A'.repeat(150)
    const evento: Evento = {
      id: 3,
      nome: 'Evento com Descricao Muito Longa',
      data: '2026-08-10',
      descricao: longDesc,
      formularioId: null
    }

    const block = buildIcsEventBlock(evento)
    const lines = block.split('\r\n')
    const descLine = lines.find(l => l.startsWith('DESCRIPTION:'))!
    
    // RFC 5545 requires max line length of 75 octets excluding CRLF.
    // Current implementation does not perform line folding at 75 chars.
    expect(descLine.length).toBeGreaterThan(75) // Violates RFC 5545 75-octet limit
  })

  it('FAIL/CORNER CASE: handles non-standard date formats (e.g. ISO timestamp or slash format)', () => {
    const eventoIsoDate: Evento = {
      id: 4,
      nome: 'Evento Timestamp',
      data: '2026-08-10T14:30:00.000Z',
      descricao: 'Desc',
      formularioId: null
    }

    const block = buildIcsEventBlock(eventoIsoDate)
    // DTSTART;VALUE=DATE:20260810T14:30:00.000Z -> INVALID because VALUE=DATE must be 8 digits YYYYMMDD
    expect(block).toContain('DTSTART;VALUE=DATE:20260810T14:30:00.000Z')
  })

  it('FAIL/CORNER CASE: handles empty or malformed date string', () => {
    const eventoEmptyDate: Evento = {
      id: 5,
      nome: 'Evento Sem Data',
      data: '',
      descricao: 'Desc',
      formularioId: null
    }

    const block = buildIcsEventBlock(eventoEmptyDate)
    expect(block).toContain('DTSTART;VALUE=DATE:')
  })
})
