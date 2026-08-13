import { useState } from 'react'
import { Bug, Wifi, AlertTriangle, Github, Sparkles } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useCrawlerStore } from '@/store/crawlerStore'
import { useCrawlerStatus } from '@/hooks/useCrawler'
import { aiApi } from '@/lib/api'
import { AiSettingsPanel } from '@/components/ai/AiSettingsPanel'
import { LanguageSwitch } from './LanguageSwitch'
import { ThemeToggle } from './ThemeToggle'

interface SidebarProps {
  onShowDisclaimer?: () => void
}

export function Sidebar({ onShowDisclaimer }: SidebarProps) {
  const { t } = useTranslation()
  const { t: tLicense } = useTranslation('license')
  const { t: tAI } = useTranslation('ai')
  const status = useCrawlerStore((state) => state.status)
  const [aiOpen, setAiOpen] = useState(false)

  // Poll status
  useCrawlerStatus()

  // Light-touch AI settings check (for configured indicator)
  useQuery({
    queryKey: ['aiSettings'],
    queryFn: async () => {
      const { data } = await aiApi.getSettings()
      return data
    },
    staleTime: 60_000,
  })

  const isRunning = status === 'running'

  return (
    <header className="h-14 flex-shrink-0 glass-panel border-b border-cyber-border-subtle relative z-10">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left: Logo and GitHub Star */}
        <div className="flex items-center gap-3">
          <Bug className="w-5 h-5 text-cyber-neon-cyan" />
          <span className="font-mono font-bold text-cyber-text-primary tracking-wider text-sm">
            MediaCrawler Pro
          </span>
          <a
            href="https://github.com/Viyozc/MediaCrawler-Pro"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-cyber-border-subtle hover:border-cyber-neon-cyan hover:shadow-glow-cyan-sm transition-all bg-cyber-bg-tertiary"
          >
            <Github className="w-4 h-4 text-cyber-text-secondary" />
            <span className="text-xs font-mono text-cyber-text-secondary">Star</span>
          </a>
          {isRunning && (
            <Badge variant="running" className="text-[10px]">
              {t('status.active')}
            </Badge>
          )}
          {isRunning && (
            <span className="w-2 h-2 bg-cyber-neon-green rounded-full shadow-glow-green-sm animate-pulse-fast" />
          )}
        </div>

        {/* Center: Warning Text */}
        <button
          onClick={onShowDisclaimer}
          className="flex items-center gap-3 px-4 py-1.5 rounded-lg border border-cyber-neon-orange/50 bg-cyber-neon-orange/10 hover:bg-cyber-neon-orange/20 transition-all cursor-pointer"
        >
          <AlertTriangle className="w-4 h-4 text-cyber-neon-orange flex-shrink-0" />
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="text-cyber-neon-orange">
              <span className="text-cyber-neon-pink font-bold">1.</span> {tLicense('content.line1')}
            </span>
            <span className="text-cyber-neon-orange">
              <span className="text-cyber-neon-pink font-bold">2.</span> {tLicense('content.line2')}
            </span>
          </div>
        </button>

        {/* Right: Actions and Status */}
        <div className="flex items-center gap-3">
          {/* AI Settings */}
          <Button
            variant="ghost"
            size="sm"
            className="font-mono text-xs text-cyber-neon-cyan hover:bg-cyber-neon-cyan/10"
            onClick={() => setAiOpen(true)}
            title={tAI('settings.open')}
          >
            <Sparkles className="w-4 h-4" />
            <span className="hidden md:inline ml-1">{tAI('settings.title')}</span>
          </Button>

          {/* Theme Toggle */}
          <ThemeToggle />
          {/* Language Switch */}
          <LanguageSwitch />

          {/* Status Info */}
          <div className="hidden lg:flex items-center gap-2 text-xs font-mono">
            <span className="text-cyber-text-muted">{t('sidebar.api')}:</span>
            <span className="text-cyber-neon-green">v1.0.0</span>
            <div className="flex items-center gap-1.5">
              <Wifi className="w-3 h-3 text-cyber-text-secondary" />
              <span className="text-cyber-text-secondary">{t('sidebar.local')}</span>
              <span className="status-dot status-dot-online" />
            </div>
          </div>
        </div>
      </div>

      <AiSettingsPanel open={aiOpen} onOpenChange={setAiOpen} />
    </header>
  )
}
