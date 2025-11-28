import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Send, X, Loader2, AlertCircle, CheckCircle2, Cpu } from "lucide-react";
import { Button } from "../../shared/components/ui/button";
import { Textarea } from "../../shared/components/ui/textarea";
import { ScrollArea } from "../../shared/components/ui/scroll-area";
import { Badge } from "../../shared/components/ui/badge";
import JigsawIcon from "../../../demo/components/JigsawIcon";

type ChatState = "idle" | "waiting" | "error" | "completed";
type Provider = "xai";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface DesignChatProps {
  /** Backend API URL (optional, for display purposes) */
  backendUrl?: string;
  /** Whether analysis is currently running */
  isAnalyzing?: boolean;
  /** Whether analysis has completed successfully */
  isCompleted?: boolean;
  /** Number of parts selected (for completion message) */
  partsCount?: number;
  /** Callback when user sends a query (triggers component analysis) */
  onQuerySent?: (query: string, provider: Provider) => void;
  /** Callback to reset/clear everything */
  onQueryKilled?: () => void;
}

export default function DesignChat({
  backendUrl: _backendUrl,
  isAnalyzing = false,
  isCompleted = false,
  partsCount = 0,
  onQuerySent,
  onQueryKilled,
}: DesignChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [provider] = useState<Provider>("xai");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Update state based on props
  const state: ChatState = isAnalyzing ? "waiting" : error ? "error" : isCompleted ? "completed" : "idle";
  
  // Add completion message when analysis completes
  useEffect(() => {
    if (isCompleted && !isAnalyzing && !messages.some(m => m.content.includes("Analysis complete") || m.content.includes("✓"))) {
      const completionMessage = partsCount > 0 
        ? `✓ Analysis complete! ${partsCount} part(s) selected and ready for design.`
        : "✓ Analysis complete. Review the results above.";
      addMessage("assistant", completionMessage);
    }
  }, [isCompleted, isAnalyzing, partsCount]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = (type: Message["type"], content: string) => {
    const newMessage: Message = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      type,
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const killQuery = () => {
    setError(null);
    setMessages([]);
    setInput("");

    if (onQueryKilled) {
      onQueryKilled();
    }
  };


  const sendQuery = (query: string) => {
    if (!query.trim() || isAnalyzing) return;

    setError(null);
    addMessage("user", query);
    setInput("");

    // Trigger component analysis via parent callback with provider
    if (onQuerySent) {
      onQuerySent(query, provider);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuery(input.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full h-[20vh] min-h-[280px] max-h-[400px] bg-gradient-to-b from-zinc-900 via-zinc-950 to-zinc-900 border-t border-zinc-800/50 flex flex-col overflow-hidden backdrop-blur-xl">
      <div className="px-4 py-3 border-b border-zinc-800/50 bg-zinc-900/40 backdrop-blur-sm flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="relative">
            {state === "completed" ? (
              <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
            ) : state === "waiting" ? (
              <>
                <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></div>
                <div className="absolute inset-0 w-2 h-2 rounded-full bg-blue-400/30 animate-ping"></div>
              </>
            ) : (
              <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
            )}
          </div>
          <h3 className="text-sm font-semibold text-zinc-200 tracking-wide">
            Component Analysis
          </h3>
          {state !== "idle" && (
            <Badge
              variant="outline"
              className={`text-[10px] ${
                state === "waiting"
                  ? "border-blue-500/50 text-blue-400 bg-blue-500/10"
                  : state === "completed"
                  ? "border-emerald-500/50 text-emerald-400 bg-emerald-500/10"
                  : "border-red-500/50 text-red-400 bg-red-500/10"
              }`}>
              {state === "waiting" && "Analyzing"}
              {state === "completed" && "Complete"}
              {state === "error" && "Error"}
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={killQuery}
          className="h-7 px-2 text-xs text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          title="Reset everything (clear chat and stop analysis)">
          <X className="w-3 h-3 mr-1" />
          Reset
        </Button>
      </div>

      <ScrollArea className="flex-1 relative min-h-0">
        <div className="p-4 space-y-5 relative">
          {messages.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none px-4 pt-16">
              <div className="text-center space-y-3 w-full max-w-sm mx-auto">
                <div className="flex justify-center items-center">
                  <div className="relative flex items-center justify-center w-20 h-20 sm:w-24 sm:h-24 overflow-visible">
                    <JigsawIcon className="opacity-40 w-full h-full" />
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                      <div className="w-1 h-1 rounded-full bg-emerald-400/60 animate-pulse"></div>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-zinc-500 font-medium tracking-wide">
                  Ready to analyze components
                </p>
                <p className="text-xs text-zinc-600">Send a query to begin</p>
              </div>
            </div>
          )}
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.96 }}
                transition={{ duration: 0.2 }}
                className={`flex gap-2.5 ${
                  message.type === "user" ? "justify-end" : "justify-start"
                }`}>
                {message.type !== "user" && (
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-zinc-800 to-zinc-900 border border-zinc-700/50 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                    <Cpu className="w-2.5 h-2.5 text-emerald-400" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] rounded-lg px-3.5 py-2.5 backdrop-blur-sm ${
                    message.type === "user"
                      ? "bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 text-emerald-50 border border-emerald-500/40 shadow-lg shadow-emerald-500/10"
                      : "bg-gradient-to-br from-zinc-800/80 to-zinc-900/80 text-zinc-200 border border-zinc-700/50 shadow-sm"
                  }`}>
                  <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
                    {message.content}
                  </p>
                  <p className="text-[10px] mt-1.5 opacity-50 font-mono">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                {message.type === "user" && (
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                    <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          {isAnalyzing && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-2.5 justify-start">
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-zinc-800 to-zinc-900 border border-zinc-700/50 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                <Loader2 className="w-2.5 h-2.5 text-blue-400 animate-spin" />
              </div>
              <div className="bg-gradient-to-br from-zinc-800/80 to-zinc-900/80 text-zinc-300 border border-zinc-700/50 rounded-lg px-3.5 py-2.5 backdrop-blur-sm shadow-sm">
                <p className="text-sm text-zinc-400 flex items-center gap-2">
                  <span className="inline-block w-1 h-1 rounded-full bg-blue-400 animate-pulse"></span>
                  Processing...
                </p>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} className="h-2" />
        </div>
      </ScrollArea>


      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-zinc-800/50 bg-zinc-900/30 backdrop-blur-sm flex-shrink-0">
        {/* Provider Selection */}
        <div className="mb-2 flex items-center gap-2">
          <div className="text-xs text-zinc-500">
            AI Provider: <span className="text-emerald-400">XAI (Grok)</span>
          </div>
        </div>
        <div className="flex gap-2.5">
          <Textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your PCB design query (e.g., 'temperature sensor with wifi and 5V-USBC')..."
            disabled={isAnalyzing}
            className="flex-1 bg-zinc-900/60 border-zinc-700/50 text-zinc-100 placeholder:text-zinc-500 placeholder:font-light resize-none min-h-[56px] max-h-[100px] rounded-lg focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all overflow-y-auto"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isAnalyzing}
            className="bg-gradient-to-br from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-white h-[56px] px-5 rounded-lg shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
            {isAnalyzing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Analyze
              </>
            )}
          </Button>
        </div>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-xs text-red-400 mt-2 flex items-center gap-1.5">
            <AlertCircle className="w-3 h-3" />
            {error}
          </motion.p>
        )}
      </form>
    </div>
  );
}
