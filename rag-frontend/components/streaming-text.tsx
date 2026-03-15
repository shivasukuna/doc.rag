"use client"

import { useEffect, useState } from "react"

interface StreamingTextProps {
  text: string
  speed?: number
}

export function StreamingText({ text, speed = 15 }: StreamingTextProps) {
  const [displayed, setDisplayed] = useState("")

  useEffect(() => {
    let index = 0
    setDisplayed("")

    const interval = setInterval(() => {
      index++
      setDisplayed(text.slice(0, index))

      if (index >= text.length) {
        clearInterval(interval)
      }
    }, speed)

    return () => clearInterval(interval)
  }, [text, speed])

  return <>{displayed}</>
}