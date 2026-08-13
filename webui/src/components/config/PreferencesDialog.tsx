import { useState, type ComponentType, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Database, KeyRound, MessageSquare, Settings2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { useCrawlerStore } from '@/store/crawlerStore'
import { useConfigOptions } from '@/hooks/useCrawler'

type SectionProps = {
  title: string
  description: string
  icon: ComponentType<{ className?: string }>
  children: ReactNode
}

function Section({ title, description, icon: Icon, children }: SectionProps) {
  return (
    <section className="rounded-lg glass-panel float-panel overflow-hidden">
      <header className="px-4 py-3 border-b border-cyber-border-subtle/50 flex items-center gap-3 bg-cyber-bg-tertiary/30">
        <div className="h-8 w-8 rounded-md bg-cyber-bg-tertiary border border-cyber-border-subtle flex items-center justify-center flex-shrink-0">
          <Icon className="h-4 w-4 text-cyber-neon-cyan" />
        </div>
        <div className="min-w-0">
          <div className="text-xs font-mono font-semibold text-cyber-text-primary tracking-wide">
            {title}
          </div>
          <div className="text-[10px] text-cyber-text-muted leading-snug truncate">
            {description}
          </div>
        </div>
      </header>
      <div className="p-4 space-y-4">{children}</div>
    </section>
  )
}

type FieldProps = {
  label: string
  hint?: string
  children: ReactNode
}

function Field({ label, hint, children }: FieldProps) {
  return (
    <div className="space-y-2">
      <div className="space-y-0.5">
        <Label className="text-xs text-cyber-text-secondary font-mono">{label}</Label>
        {hint ? (
          <p className="text-[10px] text-cyber-text-muted leading-snug">{hint}</p>
        ) : null}
      </div>
      {children}
    </div>
  )
}

interface PreferencesDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PreferencesDialog({ open, onOpenChange }: PreferencesDialogProps) {
  const { t } = useTranslation('config')
  const config = useCrawlerStore((state) => state.config)
  const updateConfig = useCrawlerStore((state) => state.updateConfig)
  const status = useCrawlerStore((state) => state.status)
  const { data: options } = useConfigOptions()

  const isDisabled = status === 'running' || status === 'stopping'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="font-mono text-cyber-neon-cyan flex items-center gap-2">
            <Settings2 className="w-4 h-4" />
            {t('preferences.title')}
          </DialogTitle>
        </DialogHeader>

        <div className="overflow-y-auto pr-2 space-y-4">
          {/* Auth Section (was Column 2 in CrawlerConfigPanel) */}
          <Section
            title={t('section.authMatrix.title')}
            description={t('section.authMatrix.description')}
            icon={KeyRound}
          >
            <Field label={t('field.loginMethod')}>
              <Select
                value={config.login_type}
                onValueChange={(value) => updateConfig({ login_type: value })}
                disabled={isDisabled}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder={t('field.loginMethodPlaceholder')} />
                </SelectTrigger>
                <SelectContent>
                  {options?.login_types.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            {config.login_type === 'cookie' ? (
              <Field label={t('field.cookies')} hint={t('field.cookiesHint')}>
                <textarea
                  value={config.cookies}
                  onChange={(e) => updateConfig({ cookies: e.target.value })}
                  disabled={isDisabled}
                  placeholder={t('field.cookiesPlaceholder')}
                  className="min-h-[80px] w-full rounded-md border border-cyber-border-DEFAULT bg-cyber-bg-tertiary px-3 py-2 text-xs font-mono text-cyber-text-primary placeholder:text-cyber-text-muted focus-visible:outline-none focus-visible:border-cyber-neon-cyan/50 focus-visible:shadow-cyber-soft disabled:cursor-not-allowed disabled:opacity-50 transition-all resize-none"
                />
              </Field>
            ) : null}

            {config.login_type === 'cookie' && (config.platform === 'xhs' || config.platform === 'dy') ? (
              <div className="rounded-lg border border-cyber-neon-orange/30 bg-cyber-neon-orange/5 p-3 text-[11px] leading-snug text-cyber-neon-orange font-mono">
                {t('warning.cookieSlider')}
              </div>
            ) : null}
          </Section>

          {/* Output Section (was Column 3 in CrawlerConfigPanel) */}
          <Section
            title={t('section.outputConfig.title')}
            description={t('section.outputConfig.description')}
            icon={Database}
          >
            <Field label={t('field.saveFormat')}>
              <Select
                value={config.save_option}
                onValueChange={(value) => updateConfig({ save_option: value })}
                disabled={isDisabled}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder={t('field.saveFormatPlaceholder')} />
                </SelectTrigger>
                <SelectContent>
                  {options?.save_options.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <div className="space-y-2">
              <div className="flex items-center gap-3 rounded-lg border border-cyber-border-subtle bg-cyber-bg-tertiary/30 p-2.5 hover:border-cyber-border-DEFAULT transition-colors">
                <Checkbox
                  checked={config.enable_comments}
                  onCheckedChange={(checked) => {
                    const isChecked = checked === true
                    updateConfig({
                      enable_comments: isChecked,
                      enable_sub_comments: isChecked ? config.enable_sub_comments : false,
                    })
                  }}
                  disabled={isDisabled}
                />
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-3.5 w-3.5 text-cyber-text-secondary" />
                  <p className="text-xs font-mono text-cyber-text-primary">
                    {t('field.commentExtraction')}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 rounded-lg border border-cyber-border-subtle bg-cyber-bg-tertiary/30 p-2.5 hover:border-cyber-border-DEFAULT transition-colors">
                <Checkbox
                  checked={config.enable_sub_comments}
                  onCheckedChange={(checked) => updateConfig({ enable_sub_comments: checked === true })}
                  disabled={isDisabled || !config.enable_comments}
                />
                <p className="text-xs font-mono text-cyber-text-primary">{t('field.subComments')}</p>
              </div>

              <div className="flex items-center gap-3 rounded-lg border border-cyber-border-subtle bg-cyber-bg-tertiary/30 p-2.5 hover:border-cyber-border-DEFAULT transition-colors">
                <Checkbox
                  checked={config.headless}
                  onCheckedChange={(checked) => updateConfig({ headless: checked === true })}
                  disabled={isDisabled}
                />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-mono text-cyber-text-primary">{t('field.headlessMode')}</p>
                  <p className="text-[10px] text-cyber-text-muted leading-snug">
                    {t('field.headlessModeHint')}
                  </p>
                </div>
              </div>
            </div>
          </Section>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/** Button + Dialog combo. Renders a gear-style trigger that opens the dialog. */
export function PreferencesButton() {
  const { t } = useTranslation('config')
  const [open, setOpen] = useState(false)
  return (
    <>
      <Button
        variant="outline"
        size="sm"
        className="font-mono text-xs"
        onClick={() => setOpen(true)}
        title={t('preferences.open')}
      >
        <Settings2 className="w-3.5 h-3.5" />
        <span className="ml-1">{t('preferences.button')}</span>
      </Button>
      <PreferencesDialog open={open} onOpenChange={setOpen} />
    </>
  )
}
