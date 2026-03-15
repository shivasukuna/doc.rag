"use client"

import { Message, MessageContent } from "@/components/ui/message"
import { Orb } from "@/components/ui/orb"
import { Response } from "@/components/ui/response"
import { useState, useRef, useEffect } from "react"
import { Paperclip, ArrowUp, FileText, Trash2, MoreHorizontal } from "lucide-react"
import { Progress } from "@/components/ui/progress"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import { ThinkingShimmer } from "@/components/thinking-shimmer"
import {
  Popover,
  PopoverContent,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Field, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useConversation } from "@/context/ConversationContext"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { toast } from "sonner"

const API_BASE = "http://127.0.0.1:8000"

export default function MainPage() {
  const {
    activeConversationId,
    setActiveConversationId,
    triggerSidebarRefresh,
  } = useConversation()

  const [messages, setMessages] = useState<any[]>([])
  const [processing, setProcessing] = useState(false)
  const [documents, setDocuments] = useState<any[]>([])

  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadedFileName, setUploadedFileName] = useState("")
  const [activeDocId, setActiveDocId] = useState<string | null>(null)

  const [mounted, setMounted] = useState(false)

useEffect(() => {
  setMounted(true)
}, [])

useEffect(() => {
  fetchDocuments()
}, [])

  const fileInputRef = useRef<HTMLInputElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const fetchDocuments = async () => {
  try {
    const res = await fetch(`${API_BASE}/documents`)
    const data = await res.json()

    if (Array.isArray(data)) {
      setDocuments(data)
    } else {
      setDocuments([])
    }
  } catch (error) {
    console.error("Failed to fetch documents:", error)
    setDocuments([])
  }
}

const deleteDocument = async (id: string) => {
  try {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: "DELETE",
    })

    const data = await res.json()
    console.log("Delete response:", data)

    if (!res.ok) {
      throw new Error(data?.error || "Failed to delete document")
    }

    // instant UI update
    setDocuments((prev) => prev.filter((doc) => doc.id !== id))

    // backend truth sync
    await fetchDocuments()

    toast("Document deleted", {
      description: "The uploaded PDF has been removed.",
    })
  } catch (err) {
    console.error("Delete failed:", err)
    toast("Failed to delete document", {
      description: "Something went wrong while deleting the PDF.",
    })
  }
}

  // 🔥 Auto scroll
  useEffect(() => {
  if (!bottomRef.current) return

  const container = bottomRef.current.parentElement?.parentElement
  if (!container) return

  container.scrollTo({
    top: container.scrollHeight - container.clientHeight - 0,
    behavior: "smooth",
  })
}, [messages])

  // 🔥 LOAD CONVERSATION WHEN ID CHANGES
  useEffect(() => {
    if (!activeConversationId) {
  setMessages([])
  return
}

    const fetchConversation = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/conversations/${activeConversationId}`
        )
        const data = await res.json()

        if (data.messages) {
          setMessages(data.messages)
        }
      } catch (error) {
        console.error("Failed to load conversation:", error)
      }
    }

    fetchConversation()
  }, [activeConversationId])

  const handleSend = () => {

  if (!input.trim() || loading) return

  const userQuery = input

  setMessages(prev => [
    ...prev,
    { role: "user", content: userQuery }
  ])

  setInput("")
  setLoading(true)

  const url =
    `${API_BASE}/chat/stream?query=${encodeURIComponent(userQuery)}&conversation_id=${activeConversationId || ""}&doc_id=${activeDocId || ""}`

  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {

    const data = JSON.parse(event.data)

    if (data.token) {

      setMessages(prev => {

        const updated = [...prev]

        const last = updated[updated.length - 1]

        if (!last || last.role !== "assistant") {

          updated.push({
            role: "assistant",
            content: data.token
          })

        } else {

          updated[updated.length - 1] = {
            ...last,
            content: last.content + data.token
          }

        }

        return updated
      })
    }

    if (data.done) {

      setActiveConversationId(data.conversation_id)
      triggerSidebarRefresh()

      setLoading(false)

      eventSource.close()
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    setLoading(false)
  }
}

 const handleFileUpload = (file: File) => {
  const formData = new FormData()
  formData.append("file", file)

  const xhr = new XMLHttpRequest()

  setUploading(true)
  setProcessing(false)
  setUploadSuccess(false)
  setUploadProgress(0)

  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      const percent = Math.round(
        (event.loaded / event.total) * 100
      )
      setUploadProgress(percent)
    }
  }

  xhr.onload = () => {
    // Upload finished, now backend is processing
    setUploading(false)
    setProcessing(true)

    const response = JSON.parse(xhr.responseText)

    if (response.doc_id) {
      setActiveDocId(response.doc_id)
      setUploadedFileName(response.filename)
      setUploadSuccess(true)
      setProcessing(false)
    }
  }

  xhr.onerror = () => {
    setUploading(false)
    setProcessing(false)
  }

  xhr.open("POST", `${API_BASE}/upload`)
  xhr.send(formData)
}

  return (
    <div className="flex flex-col h-full w-full overflow-hidden bg-background text-foreground">

      {/* Header */}
      <div className="flex items-center justify-between h-14 px-4 border-b border-border shrink-0">

  {/* LEFT */}
  <SidebarTrigger />

  {mounted && (
  <Popover onOpenChange={(open) => open && fetchDocuments()}>
    <PopoverTrigger asChild>
      <Button variant="outline" size="sm" className="gap-2">
        <FileText size={16} />
        Documents
      </Button>
    </PopoverTrigger>

    <PopoverContent align="end" className="w-72 max-h-80 overflow-y-auto">
      <PopoverHeader>
        <PopoverTitle>Uploaded Documents</PopoverTitle>
      </PopoverHeader>

      <div className="mt-3 space-y-3">
        {documents.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No documents uploaded.
          </p>
        )}

        {documents.map((doc) => (
  <div
    key={doc.id}
    className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent transition"
  >
    <div className="min-w-0">
      <p className="text-sm font-medium truncate">
        {doc.filename}
      </p>
      <p className="text-xs text-muted-foreground mt-1">
        {doc.total_pages} pages
      </p>
    </div>

    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
        >
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-36 p-2" align="end">
        <Button
          variant="ghost"
          className="w-full justify-start text-destructive hover:text-destructive"
          onClick={() => deleteDocument(doc.id)}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Delete
        </Button>
      </PopoverContent>
    </Popover>
  </div>
))}
      </div>
    </PopoverContent>
  </Popover>
  )}

</div>

      {/* Messages */}
      {/* Messages */}
<div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
  <div className="max-w-6xl mx-auto px-6 py-10 space-y-6 pb-5">

    {/* 🔥 SHOW THIS WHEN NEW CHAT */}
    {!activeConversationId && messages.length === 0 && (
      <div className="flex items-center justify-center h-full">
        <div className="opacity-70">
          {/* <img
            src="/logo/fresh1.svg"
            alt="Fresh Chat"
            className="w-190 h-90 mx-auto select-none"
          /> */}
          <p className="text-center mt-60 text-muted-foreground text-sm">
            Start a new conversation
          </p>
        </div>
      </div>
    )}

    {/* Normal Messages */}
    {messages.map((msg, i) => (

  <Message
    key={i}
    from={msg.role === "assistant" ? "assistant" : "user"}
  >

    <MessageContent>
      <Response>{msg.content}</Response>
    </MessageContent>

    {msg.role === "assistant" && (
      <div className="ring-border size-8 overflow-hidden rounded-full ring-1">
        <Orb
          className="h-full w-full"
          agentState={loading ? "talking" : null}
        />
      </div>
    )}

  </Message>

))}


    {loading && messages[messages.length - 1]?.role !== "assistant" && (

  <Message from="assistant">

    <MessageContent>
      <ThinkingShimmer />
    </MessageContent>

    <div className="ring-border size-8 overflow-hidden rounded-full ring-1">
      <Orb className="h-full w-full" agentState="talking" />
    </div>

  </Message>

)}

    <div ref={bottomRef} />
  </div>
</div>

      {/* Input */}
      <div className="shrink-0 relative">
        <div className="pointer-events-none absolute inset-x-0 -top-10 h-10 bg-gradient-to-t from-background to-transparent" />

        <div className="max-w-5xl mx-auto px-6 pb-6">
          <div className="relative bg-card/80 backdrop-blur-md border border-border rounded-2xl shadow-2xl px-4 py-4">

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="What's on your mind..."
              rows={2}
              className="w-full bg-transparent resize-none outline-none pr-16"
              onKeyDown={(e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}}
            />

            <button
              onClick={() => setDialogOpen(true)}
              className="absolute left-4 bottom-4 text-muted-foreground hover:text-foreground"
            >
              <Paperclip size={18} />
            </button>

            <button
              onClick={handleSend}
              disabled={loading}
              className="absolute right-4 bottom-4 bg-primary text-primary-foreground rounded-full p-2 disabled:opacity-50"
            >
              <ArrowUp size={18} />
            </button>

          </div>
        </div>
      </div>

      {/* Upload Dialog */}
<Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
  <DialogContent className="sm:max-w-sm">
    <DialogHeader>
      <DialogTitle>Upload Document</DialogTitle>
      <DialogDescription>
        Upload a PDF file to index it into your knowledge base.
      </DialogDescription>
    </DialogHeader>

    {/* INITIAL STATE */}
    {!uploading && !uploadSuccess && (
      <div className="space-y-4">
        <Field>
          <label>Select PDF File</label>
          <Input
            type="file"
            accept="application/pdf"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFileUpload(file)
            }}
          />
        </Field>
      </div>
    )}

    {/* UPLOADING */}
{uploading && (
  <Field className="w-full">
    <FieldLabel>
      <span>Chunking and Indexing Started</span>
      <span className="ml-auto">{uploadProgress}%</span>
    </FieldLabel>
    <Progress value={uploadProgress} />
  </Field>
)}

{/* PROCESSING */}
{processing && (
  <div className="space-y-3 text-sm text-muted-foreground">
    <p>🧠 Processing document...</p>
    <p>Indexing might take few mins</p>
  </div>
)}

{/* SUCCESS */}
{uploadSuccess && (
  <div className="space-y-2">
    <p className="font-medium text-white-500">
      Document indexed successfully.
    </p>
    <p className="text-xs text-muted-foreground">
      {uploadedFileName}
    </p>
  </div>
)}

    <DialogFooter className="mt-4">
      {!uploadSuccess ? (
        <DialogClose asChild>
          <Button variant="outline">Cancel</Button>
        </DialogClose>
      ) : (
        <Button
          onClick={() => {
            setDialogOpen(false)
            setUploadSuccess(false)
            setUploadProgress(0)
          }}
        >
          Confirm
        </Button>
      )}
    </DialogFooter>
  </DialogContent>
</Dialog>

      <input
        type="file"
        accept="application/pdf"
        hidden
        ref={fileInputRef}
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) handleFileUpload(file)
        }}
      />
    </div>
  )
}