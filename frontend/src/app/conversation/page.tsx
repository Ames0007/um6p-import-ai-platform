"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { Sparkles } from "lucide-react";
import { ChatInput } from "@/components/chat/chat-input";
import { MessageBubble } from "@/components/chat/message-bubble";
import { AssistantMessage } from "@/components/chat/assistant-message";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useCopilot } from "@/hooks/use-copilot";

function ConversationView() {
  const searchParams = useSearchParams();
  const initialQuestion = searchParams.get("q") ?? "";

  const { messages, isStreaming, send } = useCopilot();
  const [value, setValue] = React.useState("");
  const bottomRef = React.useRef<HTMLDivElement>(null);
  const seededRef = React.useRef(false);

  // Amorce la conversation avec la question passée depuis l'accueil.
  React.useEffect(() => {
    if (initialQuestion && !seededRef.current) {
      seededRef.current = true;
      send(initialQuestion);
    }
  }, [initialQuestion, send]);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col px-4">
      <ScrollArea className="flex-1">
        <div className="space-y-6 py-8">
          {messages.length === 0 ? (
            <div className="flex h-[50vh] flex-col items-center justify-center gap-3 text-center">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <Sparkles className="size-6" />
              </div>
              <p className="max-w-sm text-sm text-muted-foreground">
                Posez une question sur un produit, un code SH, les taxes, les
                autorisations ou l&apos;historique des achats. Les réponses
                proviennent exclusivement de la base de connaissances UM6P.
              </p>
            </div>
          ) : (
            messages.map((m) =>
              m.role === "user" ? (
                <MessageBubble
                  key={m.id}
                  message={{
                    id: m.id,
                    role: "user",
                    content: m.content,
                    createdAt: new Date().toISOString(),
                  }}
                />
              ) : (
                <AssistantMessage
                  key={m.id}
                  message={m}
                  onSelectCandidate={(label) => send(label)}
                />
              )
            )
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="sticky bottom-0 bg-background/80 pb-6 pt-2 backdrop-blur">
        <ChatInput
          value={value}
          onChange={setValue}
          disabled={isStreaming}
          onSubmit={(q) => {
            if (!q.trim()) return;
            send(q.trim());
            setValue("");
          }}
        />
      </div>
    </div>
  );
}

export default function ConversationPage() {
  return (
    <React.Suspense fallback={null}>
      <ConversationView />
    </React.Suspense>
  );
}
