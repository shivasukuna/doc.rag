export const API_BASE = "http://127.0.0.1:8000"

export const uploadDocument = (formData: FormData, onProgress: (percent: number) => void) => {
  return new Promise<any>((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = (event.loaded / event.total) * 100
        onProgress(Math.round(percent))
      }
    }

    xhr.onload = () => resolve(JSON.parse(xhr.responseText))
    xhr.onerror = reject

    xhr.open("POST", `${API_BASE}/upload`)
    xhr.send(formData)
  })
}

export const chatRequest = async (query: string, docId?: string) => {
  const url = `${API_BASE}/chat?query=${encodeURIComponent(query)}${
    docId ? `&doc_id=${docId}` : ""
  }`

  const res = await fetch(url)
  return res.json()
}