"use client"

import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { ConversationProvider } from "@/context/ConversationContext"
import { Toaster } from "@/components/ui/sonner"
export default function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ConversationProvider>
      <SidebarProvider>
        <div className="flex h-screen w-full overflow-hidden">

          <AppSidebar />

          <SidebarInset className="flex-1 flex flex-col overflow-hidden">
            {children}
          </SidebarInset>

          <Toaster position="top-center" expand />

        </div>
      </SidebarProvider>
    </ConversationProvider>
  )
}