"use client"

import { useState, useEffect } from "react"
import { v4 as uuidv4 } from "uuid"

export type Message = {
  role: "user" | "assistant"
  content: string
}

export type Conversation = {
  id: string
  title: string
  messages: Message[]
  createdAt: number
}

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem("conversations")
    if (saved) {
      const parsed = JSON.parse(saved)
      setConversations(parsed)
      if (parsed.length > 0) {
        setActiveId(parsed[0].id)
      }
    }
  }, [])

  useEffect(() => {
    localStorage.setItem("conversations", JSON.stringify(conversations))
  }, [conversations])

  const newConversation = () => {
    const newConv: Conversation = {
      id: uuidv4(),
      title: "New Chat",
      messages: [],
      createdAt: Date.now(),
    }

    setConversations((prev) => [newConv, ...prev])
    setActiveId(newConv.id)
  }

  const addMessage = (message: Message) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeId
          ? {
              ...conv,
              messages: [...conv.messages, message],
              title:
                conv.messages.length === 0
                  ? message.content.slice(0, 30)
                  : conv.title,
            }
          : conv
      )
    )
  }

  const activeConversation = conversations.find(
    (c) => c.id === activeId
  )

  return {
    conversations,
    activeConversation,
    activeId,
    setActiveId,
    newConversation,
    addMessage,
  }
}