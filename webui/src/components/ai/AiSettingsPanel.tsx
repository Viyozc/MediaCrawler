import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Loader2, Save, Sparkles, AlertCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { aiApi } from '@/lib/api'
import { PROVIDER_PRESETS } from '@/types/ai'
import type { AISettings, AISettingsResponse } from '@/types/ai'
import { toast } from 'sonner'

interface AiSettingsPanelProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const DEFAULTS: AISettings = {
  provider: 'openai',
  base_url: PROVIDER_PRESETS.openai.base_url,
  api_key: '',
  model: PROVIDER_PRESETS.openai.model,
  temperature: 0.7,
  max_tokens: 4096,
  system_prompt_override: null,
}

export function AiSettingsPanel({ open, onOpenChange }: AiSettingsPanelProps) {
  const { t } = useTranslation('ai')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [settings, setSettings] = useState<AISettings>(DEFAULTS)
  const [serverState, setServerState] = useState<AISettingsResponse | null>(null)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    aiApi.getSettings()
      .then(({ data }) => {
        setServerState(data)
        setSettings({
          provider: data.provider,
          base_url: data.base_url,
          // Keep existing api_key if returning user; can't recover from masked
          api_key: '',
          model: data.model,
          temperature: data.temperature,
          max_tokens: data.max_tokens,
          system_prompt_override: data.system_prompt_override,
        })
      })
      .catch(() => toast.error(t('settings.save_failed')))
      .finally(() => setLoading(false))
  }, [open, t])

  const handleProviderChange = (provider: string) => {
    const preset = PROVIDER_PRESETS[provider] ?? PROVIDER_PRESETS.custom
    setSettings((s) => ({
      ...s,
      provider,
      base_url: preset.base_url || s.base_url,
      model: preset.model || s.model,
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      // If user didn't retype api_key and we have a stored one, send the masked value
      // — backend will treat empty string as "leave unchanged"
      const toSave: AISettings = { ...settings }
      if (!toSave.api_key && serverState?.is_configured) {
        // Send a sentinel; backend will keep existing. Use a non-empty marker
        // that the user obviously wouldn't type, and tell backend to ignore.
        // Simpler: send empty and rely on backend "merge" semantics.
        // Backend's Pydantic model requires api_key: str = "", so empty is valid.
        // We need backend to preserve — so we change semantics: empty = keep existing.
      }
      const { data } = await aiApi.saveSettings(toSave)
      setServerState(data)
      toast.success(t('settings.saved'))
      onOpenChange(false)
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      toast.error(err.response?.data?.detail ?? err.message ?? t('settings.save_failed'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-cyber-neon-cyan" />
            <DialogTitle className="font-mono text-cyber-neon-cyan">
              {t('settings.title')}
            </DialogTitle>
            {serverState?.is_configured && (
              <Badge variant="outline" className="text-[10px] font-mono text-cyber-neon-green">
                {t('settings.configured')}
              </Badge>
            )}
          </div>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-cyber-neon-cyan" />
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-xs font-mono text-cyber-text-muted mb-1 block">
                {t('settings.provider')}
              </label>
              <select
                value={settings.provider}
                onChange={(e) => handleProviderChange(e.target.value)}
                className="w-full h-9 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-sm font-mono text-cyber-text-primary rounded"
              >
                {Object.entries(PROVIDER_PRESETS).map(([k, v]) => (
                  <option key={k} value={k}>{v.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-mono text-cyber-text-muted mb-1 block">
                {t('settings.base_url')}
              </label>
              <input
                type="text"
                value={settings.base_url}
                onChange={(e) => setSettings({ ...settings, base_url: e.target.value })}
                className="w-full h-9 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-sm font-mono text-cyber-text-primary rounded"
              />
            </div>

            <div>
              <label className="text-xs font-mono text-cyber-text-muted mb-1 block">
                {t('settings.api_key')}
                {serverState?.is_configured && (
                  <span className="ml-2 text-cyber-neon-green">
                    ({serverState.api_key_masked})
                  </span>
                )}
              </label>
              <input
                type="password"
                value={settings.api_key}
                onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
                placeholder={serverState?.is_configured ? '(保留已存的)' : 'sk-...'}
                className="w-full h-9 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-sm font-mono text-cyber-text-primary rounded"
              />
              <p className="text-[10px] font-mono text-cyber-text-muted mt-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {t('settings.api_key_hint')}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-mono text-cyber-text-muted mb-1 block">
                  {t('settings.model')}
                </label>
                <input
                  type="text"
                  value={settings.model}
                  onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                  className="w-full h-9 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-sm font-mono text-cyber-text-primary rounded"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-cyber-text-muted mb-1 block">
                  {t('settings.temperature')}
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={settings.temperature}
                  onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) || 0 })}
                  className="w-full h-9 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-sm font-mono text-cyber-text-primary rounded"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-mono text-cyber-text-muted mb-1 block">
                {t('settings.max_tokens')}
              </label>
              <input
                type="number"
                step="256"
                min="256"
                max="32768"
                value={settings.max_tokens}
                onChange={(e) => setSettings({ ...settings, max_tokens: parseInt(e.target.value) || 4096 })}
                className="w-full h-9 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-sm font-mono text-cyber-text-primary rounded"
              />
            </div>

            <div>
              <label className="text-xs font-mono text-cyber-text-muted mb-1 block">
                {t('settings.system_prompt_override')}
              </label>
              <textarea
                rows={3}
                value={settings.system_prompt_override ?? ''}
                onChange={(e) => setSettings({ ...settings, system_prompt_override: e.target.value || null })}
                className="w-full px-2 py-1 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-xs font-mono text-cyber-text-primary rounded"
              />
            </div>

            <div className="flex justify-end pt-2 border-t border-cyber-border-subtle">
              <Button
                onClick={handleSave}
                disabled={saving}
                className="font-mono text-sm"
              >
                {saving ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />}
                {t('settings.save')}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
