"use client"

import type * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from "@/lib/utils"

function Progress({
  className,
  value,
  gradientColor = "#444df6",
  ...props
}: React.ComponentProps<typeof ProgressPrimitive.Root> & { gradientColor?: string }) {
  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      className={cn("bg-primary/20 relative h-2 w-full overflow-hidden rounded-full", className)}
      {...props}
    >
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className="h-full w-full flex-1 transition-all"
        style={{
          transform: `translateX(-${100 - (value || 0)}%)`,
          background: `linear-gradient(to right, white, ${gradientColor})`,
        }}
      />
    </ProgressPrimitive.Root>
  )
}

export { Progress }
