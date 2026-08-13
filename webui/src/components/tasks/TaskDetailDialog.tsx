import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Loader2, FileText, MessageSquare, Trash2, X } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useTask, useTaskLogs, useDeleteTask } from '@/hooks/useTasks'
import { AgentChat } from '@/components/ai/AgentChat'
import { formatDateTime, formatFileSize } from '@/lib/utils'
import type { TaskStatus } from '@/types/task'

const STATUS_STYLES: Record<TaskStatus, string> = {
  running: 'border-cyber-neon-cyan/40 bg-cyber-neon-cyan/10 text-cyber-neon-cyan',
  completed: 'border-cyber-neon-green/40 bg-cyber-neon-green/10 text-cyber-neon-green',
  failed: 'border-red-500/40 bg-red-500/10 text-red-400',
  stopped: 'border-cyber-text-muted/40 bg-cyber-text-muted/10 text-cyber-text-muted',
}

const CONFIG_FIELDS: { key: string; label: string }[] = [
  { key: 'platform', label: 'Platform' },
  { key: 'crawler_type', label: 'Crawler Type' },
  { key: 'login_type', label: 'Login Type' },
  { key: 'keywords', label: 'Keywords' },
  { key: 'specified_ids', label: 'Specified IDs' },
  { key: 'creator_ids', label: 'Creator IDs' },
  { key: 'save_option', label: 'Save Format' },
  { key: 'headless', label: 'Headless' },
  { key: 'enable_comments', label: 'Comments' },
  { key: 'enable_sub_comments', label: 'Sub Comments' },
  { key: 'start_page', label: 'Start Page' },
  { key: 'max_notes_count', label: 'Max Notes' },
  { key: 'max_comments_count', label: 'Max Comments/Note' },
]

interface TaskDetailDialogProps {
  taskId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TaskDetailDialog({ taskId, open, onOpenChange }: TaskDetailDialogProps) {
  const { t } = useTranslation('tasks')
  const [showLogs, setShowLogs] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const deleteTask = useDeleteTask()

  const { data: task, isLoading } = useTask(open ? taskId : null)
  const { data: logs, isLoading: logsLoading } = useTaskLogs(showLogs && open ? taskId : null)

  const handleDelete = () => {
    if (!taskId) return
    if (!confirm(t('detail.delete_confirm'))) return
    deleteTask.mutate(taskId, {
      onSettled: () => onOpenChange(false),
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="font-mono text-cyber-neon-cyan">
            {task ? `${task.platform} · ${task.crawler_type}` : t('detail.title')}
          </DialogTitle>
        </DialogHeader>

        {isLoading || !task ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-5 h-5 animate-spin text-cyber-neon-cyan" />
          </div>
        ) : (
          <div className="flex flex-col gap-4 overflow-y-auto pr-2">
            {/* Status row */}
            <div className="flex items-center gap-3 flex-wrap">
              <Badge variant="outline" className={`text-[10px] font-mono ${STATUS_STYLES[task.status]}`}>
                {t(`status.${task.status}`)}
              </Badge>
              <span className="font-mono text-[10px] text-cyber-text-muted">
                {formatDateTime(task.started_at)}
                {task.ended_at && ` → ${formatDateTime(task.ended_at)}`}
              </span>
              {task.exit_code !== null && (
                <span className="font-mono text-[10px] text-cyber-text-muted">
                  {t('detail.exit_code')}: {task.exit_code}
                </span>
              )}
              <span className="font-mono text-[10px] text-cyber-text-muted truncate max-w-xs">
                {task.id}
              </span>
            </div>

            {task.error && (
              <div className="rounded border border-red-500/30 bg-red-500/5 p-2 font-mono text-xs text-red-300">
                {task.error}
              </div>
            )}

            {/* Config */}
            <div>
              <h3 className="font-mono text-xs uppercase text-cyber-neon-cyan mb-2 tracking-wider">
                {t('detail.config')}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5">
                {CONFIG_FIELDS.map(({ key, label }) => {
                  const value = (task.config as unknown as Record<string, unknown>)[key]
                  if (value === null || value === undefined || value === '' || value === false) return null
                  return (
                    <div key={key} className="flex items-center gap-2 text-xs font-mono">
                      <span className="text-cyber-text-muted">{label}</span>
                      <span className="text-cyber-text-primary truncate">
                        {typeof value === 'boolean' ? '✓' : String(value)}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Record counts */}
            {Object.keys(task.record_counts).length > 0 && (
              <div>
                <h3 className="font-mono text-xs uppercase text-cyber-neon-cyan mb-2 tracking-wider">
                  {t('detail.record_counts')}
                </h3>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(task.record_counts).map(([cat, count]) => (
                    <Badge key={cat} variant="outline" className="font-mono text-[10px] text-cyber-neon-green">
                      {cat}: {count}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Output files */}
            <div>
              <h3 className="font-mono text-xs uppercase text-cyber-neon-cyan mb-2 tracking-wider">
                {t('detail.output_files')}
              </h3>
              {task.output_files.length === 0 ? (
                <p className="font-mono text-xs text-cyber-text-muted">{t('detail.no_files')}</p>
              ) : (
                <div className="flex flex-col gap-1">
                  {task.output_files.map((f) => (
                    <a
                      key={f.path}
                      href={`/api/data/download/${f.path}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-2 px-2 py-1.5 rounded border border-cyber-border-DEFAULT hover:border-cyber-neon-cyan/40 hover:bg-cyber-neon-cyan/5 transition-colors group"
                    >
                      <FileText className="w-3 h-3 text-cyber-neon-cyan flex-shrink-0" />
                      <span className="font-mono text-xs text-cyber-text-primary truncate flex-1">{f.path}</span>
                      <span className="font-mono text-[10px] text-cyber-text-muted flex-shrink-0">
                        {formatFileSize(f.size)}
                        {f.record_count !== null && ` · ${f.record_count} rows`}
                      </span>
                    </a>
                  ))}
                </div>
              )}
            </div>

            {/* Logs */}
            {showLogs && !showChat && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-mono text-xs uppercase text-cyber-neon-cyan tracking-wider">
                    {t('logs.title')}
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 ml-auto"
                    onClick={() => setShowLogs(false)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
                <div className="rounded border border-cyber-border-DEFAULT bg-cyber-bg-panel/50 p-2 max-h-64 overflow-auto">
                  {logsLoading ? (
                    <div className="flex items-center gap-2 text-xs text-cyber-text-muted font-mono">
                      <Loader2 className="w-3 h-3 animate-spin" /> {t('logs.loading')}
                    </div>
                  ) : logs ? (
                    <pre className="font-mono text-[10px] text-cyber-text-secondary whitespace-pre-wrap break-all">{logs}</pre>
                  ) : (
                    <p className="font-mono text-xs text-cyber-text-muted">{t('logs.empty')}</p>
                  )}
                </div>
              </div>
            )}

            {/* Agent Chat */}
            {showChat && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-mono text-xs uppercase text-cyber-neon-cyan tracking-wider">
                    {t('detail.chat_with_ai')}
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 ml-auto"
                    onClick={() => setShowChat(false)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
                <AgentChat taskId={task.id} compact />
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2 border-t border-cyber-border-subtle">
              {!showLogs && !showChat && (
                <Button
                  variant="outline"
                  size="sm"
                  className="font-mono text-xs"
                  onClick={() => setShowLogs(true)}
                >
                  <FileText className="w-3 h-3 mr-1" />
                  {t('detail.view_logs')}
                </Button>
              )}
              {!showChat && (
                <Button
                  variant="outline"
                  size="sm"
                  className="font-mono text-xs text-cyber-neon-cyan hover:bg-cyber-neon-cyan/10"
                  onClick={() => { setShowChat(true); setShowLogs(false) }}
                >
                  <MessageSquare className="w-3 h-3 mr-1" />
                  {t('detail.chat_with_ai')}
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs text-red-400 hover:bg-red-500/10 ml-auto"
                onClick={handleDelete}
              >
                <Trash2 className="w-3 h-3 mr-1" />
                {t('detail.delete')}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
