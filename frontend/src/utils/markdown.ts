import { marked, type MarkedOptions } from 'marked'
import DOMPurify from 'dompurify'

export function markdownParaHtmlSeguro(texto: string, opcoesMarked?: MarkedOptions): string {
  const html = marked.parse(texto || '', opcoesMarked) as string
  return DOMPurify.sanitize(html)
}
