"use client"

import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ShimmeringText } from "@/components/ui/shimmering-text"

const phrases = [
  "Agent is thinking...",
  "Processing your request...",
  "Analyzing context...",
  "Generating response...",
  "Almost there..."
]

export function ThinkingShimmer() {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % phrases.length)
    }, 2200)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="px-1 py-2 text-sm ">
      <AnimatePresence mode="wait">
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.40 }}
        >
          <ShimmeringText text={phrases[index]} startOnView={false} />
        </motion.div>
      </AnimatePresence>
    </div>
  )
}