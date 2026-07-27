const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function comprimirImagem(file: File, max = 900, qualidade = 0.82): Promise<string> {
  return new Promise(resolve => {
    const reader = new FileReader()
    reader.onload = ev => {
      const img = new Image()
      img.onload = () => {
        let w = img.width, h = img.height
        if (w > h && w > max) { h = Math.round(h * max / w); w = max }
        else if (h > max)     { w = Math.round(w * max / h); h = max }
        const canvas = document.createElement('canvas')
        canvas.width = w; canvas.height = h
        canvas.getContext('2d')!.drawImage(img, 0, 0, w, h)
        resolve(canvas.toDataURL('image/jpeg', qualidade))
      }
      img.src = ev.target!.result as string
    }
    reader.readAsDataURL(file)
  })
}

export async function uploadImagemS3(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('attachment', file)

  const token = localStorage.getItem('caesi_admin_token')
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    const res = await fetch(`${API_BASE}/admin/attachments/upload`, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (res.ok) {
      const data = await res.json()
      const url: string = data.url
      return url.startsWith('http') ? url : `${API_BASE}${url}`
    }
  } catch (err) {
    console.error('Erro no upload para o S3:', err)
  }

  // Fallback to local data URL if S3 server is offline
  return comprimirImagem(file)
}
