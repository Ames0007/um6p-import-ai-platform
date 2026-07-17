"use client";

import { motion } from "framer-motion";
import { Sparkles, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@shared/types";

/** Bulle de message (utilisateur ou assistant). */
export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn("flex gap-3", isUser && "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-secondary text-foreground"
            : "bg-primary text-primary-foreground"
        )}
      >
        {isUser ? <User className="size-4" /> : <Sparkles className="size-4" />}
      </div>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-foreground"
        )}
      >
        {message.content}
      </div>
    </motion.div>
  );
}
