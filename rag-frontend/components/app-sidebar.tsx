"use client"

import Image from "next/image"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar"
import { MoreHorizontal, Trash2, Cpu, MemoryStick, MonitorCog } from "lucide-react"
import { toast } from "sonner"

import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover"

import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { useConversation } from "@/context/ConversationContext"
import { useEffect, useState } from "react"

const API_BASE = "http://127.0.0.1:8000"

export function AppSidebar() {
  const {
    activeConversationId,
    setActiveConversationId,
    refreshSidebar,
    triggerSidebarRefresh,
  } = useConversation()

  const [conversations, setConversations] = useState<any[]>([])

  const deleteConversation = async (id: string) => {
  try {
    await fetch(`http://127.0.0.1:8000/conversations/${id}`, {
      method: "DELETE",
    })

    triggerSidebarRefresh()

    toast.success("Conversation deleted", {
      description: "The chat has been removed.",
    })
  } catch (err) {
    toast.error("Failed to delete conversation", {
      description: "Something went wrong.",
    })
  }
}
  
  const [stats, setStats] = useState({
  cpu: 0,
  ram: 0,
  gpu: 0,
})

  const fetchSystemStats = async () => {
  try {
    const res = await fetch(`${API_BASE}/system-stats`)
    const data = await res.json()

    setStats({
      cpu: data.cpu ?? 0,
      ram: data.ram ?? 0,
      gpu: data.gpu ?? 0,
    })
  } catch (error) {
    console.error("Failed to fetch system stats:", error)
  }
}


  useEffect(() => {
  fetchSystemStats()

  const interval = setInterval(() => {
    fetchSystemStats()
  }, 3000)

  return () => clearInterval(interval)
}, [])


  const fetchConversations = async () => {
  try {
    const res = await fetch(`${API_BASE}/conversations`)
    const data = await res.json()

    if (Array.isArray(data)) {
      setConversations(data)
    } else {
      console.error("Unexpected conversations response:", data)
      setConversations([])
    }
  } catch (err) {
    console.error("Failed to fetch conversations:", err)
    setConversations([])
  }
}

  useEffect(() => {
    fetchConversations()
  }, [refreshSidebar])

  const handleNewChat = () => {
  setActiveConversationId(null)
}

  return (
    <Sidebar variant="inset" collapsible="offcanvas">
      <SidebarHeader>
        <div className="px-7 py-8">
          <Image
            src="/logo/Doc.RAG.svg"
            alt="Doc.RAG"
            width={220}
            height={40}
            priority
          />
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>

          {/* NEW CHAT BUTTON */}
          <div className="px-2 mb-6">
            <Button
              variant="secondary"
              className="w-full justify-start gap-2"
              onClick={handleNewChat}
            >
              <Plus size={16} />
              New Chat
            </Button>
          </div>

          <SidebarGroupContent>
  <SidebarMenu>
    {Array.isArray(conversations) &&
      conversations.map((conv) => (
        <SidebarMenuItem key={conv.id}>
  <div className="relative group w-full">

    <SidebarMenuButton
  isActive={activeConversationId === conv.id}
  onClick={() => setActiveConversationId(conv.id)}
  className="
  w-full pr-8
  overflow-hidden
  whitespace-nowrap
  relative
  "
>
  <span
    className="
    block overflow-hidden text-ellipsis whitespace-nowrap
    [mask-image:linear-gradient(to_right,black_75%,transparent)]
    "
  >
    {conv.title}
  </span>
</SidebarMenuButton>

    {/* 3 DOT MENU */}
    <Popover>
      <PopoverTrigger asChild>
        <button
          className="
          absolute right-2 top-1/2 -translate-y-1/2
          opacity-0 group-hover:opacity-100
          transition-all duration-200
          text-muted-foreground
          hover:text-foreground
          hover:bg-accent
          rounded-md
          p-1
          "
        >
          <MoreHorizontal size={16} />
        </button>
      </PopoverTrigger>

      <PopoverContent className="w-36 p-1">
        <button
          onClick={() => deleteConversation(conv.id)}
          className="
          flex items-center gap-2 w-full
          px-2 py-2 text-sm
          hover:bg-accent
          rounded
          "
        >
          <Trash2 size={14} />
          Delete
        </button>
      </PopoverContent>
    </Popover>

  </div>
</SidebarMenuItem>
      ))}
  </SidebarMenu>
</SidebarGroupContent>

        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
  <div className="p-3">
    <div className="rounded-2xl border border-border/60 bg-sidebar-accent/30 shadow-sm">
      <div className="border-b border-border/50 px-3 py-2">
        <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Resource Monitor
        </p>
      </div>

      <div className="space-y-3 p-3">
        {[
          { label: "CPU", value: stats.cpu, icon: Cpu },
          { label: "RAM", value: stats.ram, icon: MemoryStick },
          { label: "GPU", value: stats.gpu, icon: MonitorCog },
        ].map((stat) => {
          const Icon = stat.icon

          return (
            <div key={stat.label} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <span>{stat.label}</span>
                </div>
                <span className="text-xs tabular-nums text-muted-foreground">
                  {stat.value}%
                </span>
              </div>

              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${stat.value}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  </div>
</SidebarFooter>
    </Sidebar>
  )
}