import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Loader2, Cloud, Download } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { dataApi } from '@/lib/api'
import type { DataFile } from '@/types/crawler'

interface WordcloudDialogProps {
  file: DataFile
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface WordcloudResult {
  image_url: string
  freq_url: string
  image_path: string
  comment_count: number
}

export function WordcloudDialog({ file, open, onOpenChange }: WordcloudDialogProps) {
  const { t } = useTranslation('data')
  const [result, setResult] = useState<WordcloudResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const { data } = await dataApi.generateWordcloud({ file_path: file.path })
      setResult(data)
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err.response?.data?.detail ?? err.message ?? 'Failed')
    } finally {
      setLoading(false)
    }
  }

  // Auto-trigger when opened
  if (open && !loading && !result && !error) {
    generate()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center gap-3">
            <Cloud className="w-5 h-5 text-cyber-neon-cyan" />
            <DialogTitle className="font-mono text-cyber-neon-cyan">
              {t('wordcloud.title', { defaultValue: 'Wordcloud' })}
            </DialogTitle>
            <Badge variant="outline" className="font-mono text-[10px] text-cyber-text-muted">
              {file.name}
            </Badge>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-auto min-h-[300px]">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-cyber-neon-cyan" />
              <span className="font-mono text-xs text-cyber-text-muted">
                {t('wordcloud.generating', { defaultValue: 'Generating wordcloud...' })}
              </span>
            </div>
          )}

          {error && (
            <div className="rounded border border-red-500/30 bg-red-500/5 p-3 font-mono text-xs text-red-300">
              {error}
            </div>
          )}

          {result && (
            <div className="flex flex-col gap-3">
              <img
                src={result.image_url}
                alt="wordcloud"
                className="w-full rounded border border-cyber-border-DEFAULT bg-white"
              />
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="font-mono text-[10px] text-cyber-neon-green">
                  {result.comment_count} comments
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  className="font-mono text-xs"
                  onClick={() => window.open(result.image_url, '_blank')}
                >
                  <Download className="w-3 h-3 mr-1" />
                  PNG
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="font-mono text-xs"
                  onClick={() => window.open(result.freq_url, '_blank')}
                >
                  <Download className="w-3 h-3 mr-1" />
                  Frequencies
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
