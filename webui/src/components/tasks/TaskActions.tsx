/**
 * Per-task direct-action dialogs.
 *
 * Each task row in TaskHistoryList renders a <TaskActionButtons> with
 * chat / preview / download / logs / delete buttons. Each button opens
 * a focused dialog directly — no nesting through TaskDetailDialog.
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Download, Eye, FileText, Loader2, MessageSquare, Trash2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { dataApi } from '@/lib/api'
import { useTask, useTaskLogs, useDeleteTask } from '@/hooks/useTasks'
import { AgentChat } from '@/components/ai/AgentChat'
import { formatFileSize } from '@/lib/utils'
import type { TaskRecord } from '@/types/task'

/* ---------------- Preview ---------------- */

interface PreviewDialogProps {
  taskId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function TaskDataPreviewDialog({ taskId, open, onOpenChange }: PreviewDialogProps) {
  const { t } = useTranslation('tasks')
  const { data: task } = useTask(open ? taskId : null)
  const files = task?.output_files ?? []
  const [activePath, setActivePath] = useState<string | null>(null)

  // Pick first file by default when task loads
  useEffect(() => {
    if (task && files.length > 0 && !activePath) {
      setActivePath(files[0].path)
    }
    if (!open) setActivePath(null)
  }, [task, open, files, activePath])

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['taskFilePreview', taskId, activePath],
    queryFn: async () => {
      if (!activePath) return null
      const { data } = await dataApi.getFileContent(activePath, 100)
      return data
    },
    enabled: !!activePath && open,
  })

  const rows = preview?.data ?? []
  const columns = rows.length > 0 ? Object.keys(rows[0]) : []

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[85vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="font-mono text-cyber-neon-cyan flex items-center gap-2">
            <Eye className="w-4 h-4" />
            {t('actions.preview')}
          </DialogTitle>
        </DialogHeader>

        {files.length === 0 ? (
          <p className="font-mono text-xs text-cyber-text-muted py-6 text-center">
            {t('detail.no_files')}
          </p>
        ) : (
          <div className="flex flex-col gap-3 overflow-hidden flex-1 min-h-0">
            {/* File selector */}
            <div className="flex flex-wrap gap-1.5 flex-shrink-0">
              {files.map((f) => (
                <button
                  key={f.path}
                  onClick={() => setActivePath(f.path)}
                  className={`px-2 py-1 rounded border font-mono text-[10px] transition-colors ${
                    activePath === f.path
                      ? 'border-cyber-neon-cyan/60 bg-cyber-neon-cyan/10 text-cyber-neon-cyan'
                      : 'border-cyber-border-DEFAULT text-cyber-text-muted hover:border-cyber-neon-cyan/40'
                  }`}
                  title={f.path}
                >
                  {f.path.split('/').pop()}
                  {f.record_count !== null && (
                    <span className="ml-1 text-cyber-text-muted">({f.record_count})</span>
                  )}
                </button>
              ))}
            </div>

            {/* Table */}
            <div className="flex-1 overflow-auto rounded border border-cyber-border-DEFAULT bg-cyber-bg-panel/50">
              {previewLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-4 h-4 animate-spin text-cyber-neon-cyan" />
                </div>
              ) : rows.length === 0 ? (
                <p className="font-mono text-xs text-cyber-text-muted py-6 text-center">
                  {t('actions.no_rows')}
                </p>
              ) : (
                <table className="w-full text-xs font-mono">
                  <thead className="sticky top-0 bg-cyber-bg-tertiary/90 backdrop-blur">
                    <tr>
                      {columns.map((col) => (
                        <th
                          key={col}
                          className="text-left px-2 py-1.5 border-b border-cyber-border-subtle text-cyber-neon-cyan font-semibold truncate max-w-[200px]"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => (
                      <tr key={i} className="hover:bg-cyber-neon-cyan/5">
                        {columns.map((col) => {
                          const v = (row as Record<string, unknown>)[col]
                          const s = v === null || v === undefined ? '' : typeof v === 'object' ? JSON.stringify(v) : String(v)
                          return (
                            <td
                              key={col}
                              className="px-2 py-1 border-b border-cyber-border-subtle/30 text-cyber-text-primary truncate max-w-[200px]"
                              title={s}
                            >
                              {s}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            {preview && (
              <div className="text-[10px] font-mono text-cyber-text-muted flex-shrink-0">
                {t('actions.showing', { shown: rows.length, total: preview.total })}
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

/* ---------------- Download ---------------- */

interface DownloadDialogProps {
  taskId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function TaskDownloadDialog({ taskId, open, onOpenChange }: DownloadDialogProps) {
  const { t } = useTranslation('tasks')
  const { data: task } = useTask(open ? taskId : null)
  const files = task?.output_files ?? []

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle className="font-mono text-cyber-neon-cyan flex items-center gap-2">
            <Download className="w-4 h-4" />
            {t('actions.download')}
          </DialogTitle>
        </DialogHeader>
        {files.length === 0 ? (
          <p className="font-mono text-xs text-cyber-text-muted py-6 text-center">
            {t('detail.no_files')}
          </p>
        ) : (
          <div className="flex flex-col gap-1.5">
            {files.map((f) => (
              <a
                key={f.path}
                href={`/api/data/download/${f.path}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 px-3 py-2 rounded border border-cyber-border-DEFAULT hover:border-cyber-neon-cyan/40 hover:bg-cyber-neon-cyan/5 transition-colors"
              >
                <FileText className="w-3.5 h-3.5 text-cyber-neon-cyan flex-shrink-0" />
                <span className="font-mono text-xs text-cyber-text-primary truncate flex-1">{f.path}</span>
                <span className="font-mono text-[10px] text-cyber-text-muted flex-shrink-0">
                  {formatFileSize(f.size)}
                  {f.record_count !== null && ` · ${f.record_count} rows`}
                </span>
                <Download className="w-3 h-3 text-cyber-text-muted flex-shrink-0" />
              </a>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

/* ---------------- Logs ---------------- */

interface LogsDialogProps {
  taskId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function TaskLogsDialog({ taskId, open, onOpenChange }: LogsDialogProps) {
  const { t } = useTranslation('tasks')
  const { data: logs, isLoading } = useTaskLogs(open ? taskId : null)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="font-mono text-cyber-neon-cyan flex items-center gap-2">
            <FileText className="w-4 h-4" />
            {t('logs.title')}
          </DialogTitle>
        </DialogHeader>
        <div className="rounded border border-cyber-border-DEFAULT bg-cyber-bg-panel/50 p-2 max-h-[60vh] overflow-auto">
          {isLoading ? (
            <div className="flex items-center gap-2 text-xs text-cyber-text-muted font-mono">
              <Loader2 className="w-3 h-3 animate-spin" /> {t('logs.loading')}
            </div>
          ) : logs ? (
            <pre className="font-mono text-[10px] text-cyber-text-secondary whitespace-pre-wrap break-all">{logs}</pre>
          ) : (
            <p className="font-mono text-xs text-cyber-text-muted">{t('logs.empty')}</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

/* ---------------- Chat ---------------- */

interface ChatDialogProps {
  taskId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function TaskChatDialog({ taskId, open, onOpenChange }: ChatDialogProps) {
  const { t } = useTranslation('tasks')
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="font-mono text-cyber-neon-cyan flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            {t('detail.chat_with_ai')}
            {taskId && (
              <span className="font-mono text-[10px] text-cyber-text-muted truncate max-w-[200px]">
                {taskId}
              </span>
            )}
          </DialogTitle>
        </DialogHeader>
        {taskId && <AgentChat taskId={taskId} compact />}
      </DialogContent>
    </Dialog>
  )
}

/* ---------------- Row Action Buttons ---------------- */

type DialogKind = 'chat' | 'preview' | 'download' | 'logs' | null

interface TaskActionButtonsProps {
  task: TaskRecord
  onOpenDialog: (kind: DialogKind, taskId: string) => void
}

export function TaskActionButtons({ task, onOpenDialog }: TaskActionButtonsProps) {
  const { t } = useTranslation('tasks')
  const deleteTask = useDeleteTask()
  const hasFiles = task.output_files.length > 0

  return (
    <div className="ml-auto flex items-center gap-0.5">
      <Button
        variant="ghost"
        size="sm"
        className="h-7 px-2 font-mono text-xs text-cyber-neon-cyan hover:bg-cyber-neon-cyan/10 border border-cyber-neon-cyan/30 hover:border-cyber-neon-cyan/60"
        onClick={(e) => {
          e.stopPropagation()
          onOpenDialog('chat', task.id)
        }}
        title={t('detail.chat_with_ai')}
        disabled={!hasFiles}
      >
        <MessageSquare className="w-3 h-3 mr-1" />
        {t('actions.chat')}
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-7 p-0 text-cyber-neon-cyan hover:bg-cyber-neon-cyan/10"
        onClick={(e) => {
          e.stopPropagation()
          onOpenDialog('preview', task.id)
        }}
        title={t('actions.preview')}
        disabled={!hasFiles}
      >
        <Eye className="w-3 h-3" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-7 p-0 text-cyber-neon-green hover:bg-cyber-neon-green/10"
        onClick={(e) => {
          e.stopPropagation()
          onOpenDialog('download', task.id)
        }}
        title={t('actions.download')}
        disabled={!hasFiles}
      >
        <Download className="w-3 h-3" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-7 p-0 text-cyber-text-secondary hover:bg-cyber-border-subtle/30"
        onClick={(e) => {
          e.stopPropagation()
          onOpenDialog('logs', task.id)
        }}
        title={t('logs.title')}
      >
        <FileText className="w-3 h-3" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-7 p-0 text-red-400 hover:bg-red-500/10"
        onClick={(e) => {
          e.stopPropagation()
          if (confirm(t('detail.delete_confirm'))) {
            deleteTask.mutate(task.id)
          }
        }}
        title={t('detail.delete')}
      >
        <Trash2 className="w-3 h-3" />
      </Button>
    </div>
  )
}

/* ---------------- Dialog Host (single component manages all 4 dialogs) ---------------- */

export function TaskActionDialogs() {
  const [dialogKind, setDialogKind] = useState<DialogKind>(null)
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)

  const open = (kind: DialogKind, taskId: string) => {
    setActiveTaskId(taskId)
    setDialogKind(kind)
  }
  const close = () => {
    setDialogKind(null)
    setActiveTaskId(null)
  }

  return {
    openDialog: open,
    dialog: (
      <>
        <TaskChatDialog
          taskId={activeTaskId}
          open={dialogKind === 'chat'}
          onOpenChange={(o) => !o && close()}
        />
        <TaskDataPreviewDialog
          taskId={activeTaskId}
          open={dialogKind === 'preview'}
          onOpenChange={(o) => !o && close()}
        />
        <TaskDownloadDialog
          taskId={activeTaskId}
          open={dialogKind === 'download'}
          onOpenChange={(o) => !o && close()}
        />
        <TaskLogsDialog
          taskId={activeTaskId}
          open={dialogKind === 'logs'}
          onOpenChange={(o) => !o && close()}
        />
      </>
    ),
  }
}
