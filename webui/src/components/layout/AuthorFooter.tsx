/**
 * Project attribution footer (upstream credit, no personal promo).
 */
import { useTranslation } from 'react-i18next'
import { Github, Heart } from 'lucide-react'

const REPO_URL = 'https://github.com/Viyozc/MediaCrawler-Pro'
const UPSTREAM_URL = 'https://github.com/NanmiCoder/MediaCrawler'

export function AuthorFooter() {
  const { t } = useTranslation('license')

  return (
    <footer className="h-20 flex-shrink-0 glass-panel border-t border-cyber-border-subtle">
      <div className="h-full px-6 flex items-center justify-center gap-4 flex-wrap">
        <div className="flex flex-col gap-0.5 min-w-0">
          <span className="text-sm font-bold text-cyber-text-primary truncate">
            {t('author.name')}
          </span>
          <span className="text-xs text-cyber-text-muted truncate hidden sm:inline">
            {t('author.description')}
          </span>
          <div className="flex items-center gap-1.5 text-cyber-neon-cyan">
            <Heart className="w-3.5 h-3.5 fill-current" />
            <span className="text-xs font-medium">{t('author.slogan')}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="h-9 px-3 rounded-lg flex items-center gap-1.5 border border-cyber-border-subtle hover:border-cyber-neon-cyan hover:shadow-glow-cyan-sm transition-all bg-cyber-bg-tertiary font-mono text-xs text-cyber-text-secondary"
            title="GitHub"
          >
            <Github className="w-4 h-4" />
            MediaCrawler Pro
          </a>
          <a
            href={UPSTREAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="h-9 px-3 rounded-lg flex items-center gap-1.5 border border-cyber-border-subtle hover:border-cyber-neon-cyan/60 transition-all bg-cyber-bg-tertiary font-mono text-xs text-cyber-text-muted"
            title={t('author.upstream')}
          >
            Upstream
          </a>
        </div>
      </div>
    </footer>
  )
}
