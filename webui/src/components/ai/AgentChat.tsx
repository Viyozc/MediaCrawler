import { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Loader2, Send, Sparkles, Settings2, AlertCircle, Eraser } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from '@/components/ui/button'
import { aiApi, AI_CHAT_URL } from '@/lib/api'
import { AiSettingsPanel } from './AiSettingsPanel'
import type { ChatMessage, AISettingsResponse } from '@/types/ai'
import { toast } from 'sonner'

interface AgentChatProps {
  taskId: string
  /** Compact mode: rendered inside a Dialog. */
  compact?: boolean
}

interface StreamState {
  messages: ChatMessage[]
  streaming: boolean
  error: string | null
}

const INITIAL: StreamState = { messages: [], streaming: false, error: null }

export function AgentChat({ taskId, compact = false }: AgentChatProps) {
  const { t } = useTranslation('ai')
  const [state, setState] = useState<StreamState>(INITIAL)
  const [input, setInput] = useState('')
  const [includeFull, setIncludeFull] = useState(false)
  const [sampleSize, setSampleSize] = useState(20)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Load AI config + chat history on mount
  const { data: settingsData } = useQuery({
    queryKey: ['aiSettings'],
    queryFn: async () => {
      const { data } = await aiApi.getSettings()
      return data as AISettingsResponse
    },
  })

  useEffect(() => {
    if (settingsData) setIsConfigured(settingsData.is_configured)
  }, [settingsData])

  const { data: historyData } = useQuery({
    queryKey: ['aiChatHistory', taskId],
    queryFn: async () => {
      const { data } = await aiApi.getChatHistory(taskId)
      return data
    },
    enabled: !!taskId,
  })

  useEffect(() => {
    if (historyData?.messages?.length) {
      setState({ messages: historyData.messages, streaming: false, error: null })
    }
  }, [historyData])

  // Auto-scroll on new content
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [state.messages, state.streaming])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || state.streaming) return
    if (!isConfigured) {
      setSettingsOpen(true)
      return
    }

    const userMsg: ChatMessage = { role: 'user', content: text }
    const priorMessages = [...state.messages, userMsg]
    setState({
      messages: priorMessages,
      streaming: true,
      error: null,
    })
    setInput('')

    const ac = new AbortController()
    abortRef.current = ac

    // Append a streaming assistant message
    const startLen = priorMessages.length
    try {
      const resp = await fetch(AI_CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          messages: [{ role: 'user', content: text }],
          include_full_data: includeFull,
          sample_size: sampleSize,
        }),
        signal: ac.signal,
      })

      if (!resp.ok || !resp.body) {
        const detail = await resp.text().catch(() => resp.statusText)
        throw new Error(detail)
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let assistantText = ''

      // Stream loop
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() ?? ''
        for (const ev of events) {
          const line = ev.trim()
          if (!line.startsWith('data:')) continue
          const payload = line.slice(5).trim()
          try {
            const obj = JSON.parse(payload)
            if (obj.type === 'token') {
              assistantText += obj.content
              setState((s) => {
                const msgs = [...s.messages]
                if (msgs.length === startLen) {
                  msgs.push({ role: 'assistant', content: assistantText })
                } else if (msgs.length > startLen) {
                  msgs[msgs.length - 1] = { role: 'assistant', content: assistantText }
                }
                return { ...s, messages: msgs }
              })
            } else if (obj.type === 'error') {
              setState((s) => ({
                ...s,
                streaming: false,
                error: t('chat.error', { message: obj.message ?? '' }),
              }))
              return
            } else if (obj.type === 'done') {
              setState((s) => ({ ...s, streaming: false }))
              return
            }
          } catch {
            // ignore malformed event
          }
        }
      }
      setState((s) => ({ ...s, streaming: false }))
    } catch (e) {
      const err = e as Error
      if (err.name === 'AbortError') return
      setState((s) => ({
        ...s,
        streaming: false,
        error: t('chat.error', { message: err.message }),
      }))
    } finally {
      abortRef.current = null
    }
  }, [input, state.streaming, state.messages, isConfigured, taskId, includeFull, sampleSize, t])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const clearChat = async () => {
    if (!confirm(t('chat.clear_confirm'))) return
    setState({ messages: [], streaming: false, error: null })
    toast.success(t('chat.clear'))
  }

  return (
    <div className={`flex flex-col gap-2 ${compact ? 'h-[60vh]' : 'h-full'}`}>
      {/* Header */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <Sparkles className="w-4 h-4 text-cyber-neon-cyan" />
        <span className="font-mono text-sm text-cyber-neon-cyan">{t('chat.title')}</span>
        <span className="font-mono text-[10px] text-cyber-text-muted truncate">{taskId}</span>
        <div className="ml-auto flex items-center gap-1">
          {state.messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 font-mono text-xs text-cyber-text-muted"
              onClick={clearChat}
              title={t('chat.clear')}
            >
              <Eraser className="w-3 h-3" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 font-mono text-xs text-cyber-neon-cyan"
            onClick={() => setSettingsOpen(true)}
            title={t('settings.open')}
          >
            <Settings2 className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {/* Not configured banner */}
      {isConfigured === false && (
        <div className="rounded border border-cyber-neon-orange/30 bg-cyber-neon-orange/5 p-3 flex items-center gap-3">
          <AlertCircle className="w-4 h-4 text-cyber-neon-orange flex-shrink-0" />
          <span className="font-mono text-xs text-cyber-neon-orange flex-1">
            {t('chat.not_configured')}
          </span>
          <Button
            variant="outline"
            size="sm"
            className="font-mono text-xs"
            onClick={() => setSettingsOpen(true)}
          >
            {t('chat.open_settings')}
          </Button>
        </div>
      )}

      {/* Messages */}
      <div
        ref={scrollRef}
        className={`flex-1 overflow-auto rounded border border-cyber-border-DEFAULT bg-cyber-bg-panel/50 p-3 ${compact ? 'min-h-[300px]' : ''}`}
      >
        {state.messages.length === 0 && !state.streaming && (
          <div className="text-center text-cyber-text-muted py-8 font-mono text-xs">
            {t('chat.placeholder')}
          </div>
        )}
        <div className="flex flex-col gap-3">
          {state.messages.map((msg, i) => (
            <div
              key={i}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <span className="text-[10px] font-mono text-cyber-text-muted mb-1">
                {msg.role === 'user' ? t('chat.you') : t('chat.assistant')}
              </span>
              <div
                className={`max-w-[90%] px-3 py-2 rounded-lg text-xs break-words ${
                  msg.role === 'user'
                    ? 'bg-cyber-neon-cyan/15 border border-cyber-neon-cyan/30 text-cyber-text-primary font-mono whitespace-pre-wrap'
                    : 'bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-cyber-text-primary agent-chat-md'
                }`}
              >
                {msg.role === 'user' ? (
                  msg.content
                ) : (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                )}
              </div>
            </div>
          ))}
          {state.streaming && state.messages[state.messages.length - 1]?.role === 'user' && (
            <div className="flex items-center gap-2 text-cyber-text-muted">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span className="font-mono text-[10px]">{t('chat.streaming')}</span>
            </div>
          )}
        </div>
        {state.error && (
          <div className="mt-3 rounded border border-red-500/30 bg-red-500/5 p-2 font-mono text-xs text-red-300">
            {state.error}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-shrink-0 flex-wrap">
        <label className="flex items-center gap-1.5 font-mono text-xs text-cyber-text-muted">
          <input
            type="checkbox"
            checked={includeFull}
            onChange={(e) => setIncludeFull(e.target.checked)}
            className="accent-cyber-neon-cyan"
          />
          {t('chat.include_full_data')}
        </label>
        <label className="flex items-center gap-1.5 font-mono text-xs text-cyber-text-muted">
          {t('chat.sample_size')}
          <input
            type="number"
            min={1}
            max={500}
            value={sampleSize}
            onChange={(e) => setSampleSize(parseInt(e.target.value) || 20)}
            className="w-16 h-7 px-1 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-xs font-mono text-cyber-text-primary rounded"
          />
        </label>
      </div>

      {/* Input */}
      <div className="flex gap-2 flex-shrink-0">
        <textarea
          rows={compact ? 2 : 3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.placeholder')}
          className="flex-1 px-3 py-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-sm font-mono text-cyber-text-primary rounded resize-none focus:border-cyber-neon-cyan/50 focus:outline-none"
        />
        <Button
          onClick={send}
          disabled={state.streaming || !input.trim()}
          className="font-mono text-sm self-stretch"
        >
          {state.streaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </Button>
      </div>

      <AiSettingsPanel open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  )
}
