"use client"

import { memo, type ComponentProps } from "react"
import { Streamdown } from "streamdown"

import { cn } from "@/lib/utils"

type ResponseProps = ComponentProps<typeof Streamdown>

export const Response = memo(
  ({ className, ...props }: ResponseProps) => (
    <Streamdown
      className={cn(
  "size-full leading-relaxed break-words",
  "[&_ul]:pl-6 [&_ol]:pl-6",
  "[&_li]:ml-1",
  "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
  className
)}

      {...props}
    />
  ),
  (prevProps, nextProps) => prevProps.children === nextProps.children
)

Response.displayName = "Response"
