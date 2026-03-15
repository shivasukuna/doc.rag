"use client"

import { createContext, useContext, useState } from "react"

interface ConversationContextType {
  activeConversationId: string | null
  setActiveConversationId: (id: string | null) => void
  refreshSidebar: boolean
  triggerSidebarRefresh: () => void
}

const ConversationContext = createContext<ConversationContextType | null>(null)

export function ConversationProvider({ children }: { children: React.ReactNode }) {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [refreshSidebar, setRefreshSidebar] = useState(false)

  const triggerSidebarRefresh = () => {
    setRefreshSidebar((prev) => !prev)
  }

  return (
    <ConversationContext.Provider
      value={{
        activeConversationId,
        setActiveConversationId,
        refreshSidebar,
        triggerSidebarRefresh,
      }}
    >
      {children}
    </ConversationContext.Provider>
  )
}

export function useConversation() {
  const context = useContext(ConversationContext)
  if (!context) {
    throw new Error("useConversation must be used inside ConversationProvider")
  }
  return context
}