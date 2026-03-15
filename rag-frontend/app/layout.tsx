import type { Metadata } from "next"
import localFont from "next/font/local"
import "./globals.css"

const jetbrainsMono = localFont({
  src: [
    {
      path: "./fonts/JetBrainsMono-Regular.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "./fonts/JetBrainsMono-Medium.woff2",
      weight: "500",
      style: "normal",
    },
    {
      path: "./fonts/JetBrainsMono-Bold.woff2",
      weight: "700",
      style: "normal",
    },
    {
      path: "./fonts/JetBrainsMono-Italic.woff2",
      weight: "400",
      style: "italic",
    },
    {
      path: "./fonts/JetBrainsMono-Medium-Italic.woff2",
      weight: "500",
      style: "italic",
    },
    {
      path: "./fonts/JetBrainsMono-ExtraBold.woff2",
      weight: "800",
      style: "normal",
    },
    {
      path: "./fonts/JetBrainsMono-ExtraBold-Italic.woff2",
      weight: "800",
      style: "italic",
    },
  ],
  variable: "--font-jetbrains",
  display: "swap",
})

export const metadata: Metadata = {
  title: "Doc.RAG",
  description: "Local RAG System",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${jetbrainsMono.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}