export interface AISettings {
  provider: string
  base_url: string
  api_key: string
  model: string
  temperature: number
  max_tokens: number
  system_prompt_override: string | null
}

export interface AISettingsResponse {
  provider: string
  base_url: string
  api_key_masked: string
  model: string
  temperature: number
  max_tokens: number
  system_prompt_override: string | null
  is_configured: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  ts?: string
}

export interface ChatHistoryResponse {
  messages: ChatMessage[]
  task_id: string
}

export const PROVIDER_PRESETS: Record<string, { base_url: string; model: string; label: string }> = {
  openai: { base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini', label: 'OpenAI' },
  deepseek: { base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat', label: 'DeepSeek' },
  qwen: { base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus', label: '通义千问 (Qwen)' },
  ollama: { base_url: 'http://localhost:11434/v1', model: 'qwen2.5', label: 'Ollama (本地)' },
  lmstudio: { base_url: 'http://localhost:1234/v1', model: 'local-model', label: 'LM Studio (本地)' },
  openrouter: { base_url: 'https://openrouter.ai/api/v1', model: 'anthropic/claude-3.5-sonnet', label: 'OpenRouter' },
  custom: { base_url: '', model: '', label: '自定义 (Custom)' },
}
