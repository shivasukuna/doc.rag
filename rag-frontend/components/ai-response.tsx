// components/ai-response.tsx

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

export function AIResponse({ content }: { content: string }) {
  return (
    <div
      className="
        max-w-[80%]
        min-w-0
        overflow-hidden
        rounded-2xl
        border
        border-border
        bg-card
        px-6
        py-5
        shadow-sm
      "
    >
      <div
        className="
          prose
    dark:prose-invert
    max-w-full
    break-words
    [overflow-wrap:anywhere]
    [&_*]:break-words
    prose-pre:whitespace-pre-wrap
    prose-pre:break-words
    prose-pre:[overflow-wrap:anywhere]
    prose-pre:overflow-x-auto
    prose-table:block
    prose-table:overflow-x-auto
  prose-p:leading-7
  prose-p:my-3
  prose-h2:mt-8
  prose-h3:mt-6
  prose-ul:my-4
  prose-li:my-1
    
        "
      >
        <ReactMarkdown
  remarkPlugins={[remarkGfm]}
>
  {content}
</ReactMarkdown>
      </div>
    </div>
  )
}