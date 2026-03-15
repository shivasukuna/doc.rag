"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Progress } from "@/components/ui/progress"

export default function Home() {
  const [progress, setProgress] = useState(0)
  const [fadeOut, setFadeOut] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setFadeOut(true)
          setTimeout(() => {
            router.push("/main")
          }, 600)
          return 100
        }
        return prev + 5
      })
    }, 100)

    return () => clearInterval(interval)
  }, [router])

  return (
    <div
      className={`min-h-screen flex flex-col items-center justify-center transition-opacity duration-700 ease-in-out ${
        fadeOut ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className="w-full max-w-md space-y-6 text-center">
        <img
  src="/logo/Doc.RAG.svg"
  alt="Doc.RAG"
  className="w-[320px] md:w-[420px] mx-auto"
  />

        <Progress value={progress} />
      </div>
    </div>
  )
}
