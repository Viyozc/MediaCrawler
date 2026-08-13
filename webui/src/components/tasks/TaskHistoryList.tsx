import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Loader2, History } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useTaskList } from '@/hooks/useTasks'
import { TaskDetailDialog } from './TaskDetailDialog'
import { TaskActionButtons, TaskActionDialogs } from './TaskActions'
import { formatDateTime, formatFileSize } from '@/lib/utils'
import type { TaskStatus } from '@/types/task'

const STATUS_STYLES: Record<TaskStatus, string> = {
  running: 'border-cyber-neon-cyan/40 bg-cyber-neon-cyan/10 text-cyber-neon-cyan',
  completed: 'border-cyber-neon-green/40 bg-cyber-neon-green/10 text-cyber-neon-green',
  failed: 'border-red-500/40 bg-red-500/10 text-red-400',
  stopped: 'border-cyber-text-muted/40 bg-cyber-text-muted/10 text-cyber-text-muted',
}

const PLATFORM_LABELS: Record<string, string> = {
  xhs: '小红书',
  dy: '抖音',
  ks: '快手',
  bili: '哔哩哔哩',
  wb: '微博',
  tieba: '贴吧',
  zhihu: '知乎',
}

function formatDuration(startedAt: string, endedAt: string | null): string {
  const start = new Date(startedAt).getTime()
  const end = endedAt ? new Date(endedAt).getTime() : Date.now()
  const seconds = Math.max(0, Math.floor((end - start) / 1000))
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m < 60) return `${m}m ${s}s`
  const h = Math.floor(m / 60)
  return `${h}h ${m % 60}m`
}

export function TaskHistoryList() {
  const { t } = useTranslation('tasks')
  const [statusFilter, setStatusFilter] = useState<TaskStatus | ''>('')
  const [platformFilter, setPlatformFilter] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { openDialog, dialog: actionDialogs } = TaskActionDialogs()

  const params: Record<string, string | number> = { page: 1, page_size: 50 }
  if (statusFilter) params.status = statusFilter
  if (platformFilter) params.platform = platformFilter

  const { data, isLoading, error } = useTaskList(params)

  if (error) {
    return (
      <div className="text-center text-cyber-text-muted py-8 font-mono text-sm">
        {t('empty')} — {String(error)}
      </div>
    )
  }

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center py-12 text-cyber-text-muted">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        <span className="font-mono text-sm">Loading...</span>
      </div>
    )
  }

  const tasks = data?.tasks ?? []

  return (
    <div className="h-full flex flex-col gap-3 overflow-hidden">
      {/* Filters */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <History className="w-4 h-4 text-cyber-neon-cyan" />
        <span className="font-mono text-sm text-cyber-neon-cyan">{t('title')}</span>
        <div className="ml-auto flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as TaskStatus | '')}
            className="cyber-select h-8 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-xs font-mono text-cyber-text-primary rounded"
          >
            <option value="">{t('filter.all')}</option>
            <option value="running">{t('status.running')}</option>
            <option value="completed">{t('status.completed')}</option>
            <option value="failed">{t('status.failed')}</option>
            <option value="stopped">{t('status.stopped')}</option>
          </select>
          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
            className="cyber-select h-8 px-2 bg-cyber-bg-tertiary border border-cyber-border-DEFAULT text-xs font-mono text-cyber-text-primary rounded"
          >
            <option value="">{t('filter.all')}</option>
            {Object.entries(PLATFORM_LABELS).map(([v, label]) => (
              <option key={v} value={v}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-auto pr-1">
        {tasks.length === 0 ? (
          <div className="text-center text-cyber-text-muted py-12 font-mono text-sm">
            {statusFilter || platformFilter ? t('empty_filtered') : t('empty')}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {tasks.map((task) => {
              const recordTotal = Object.values(task.record_counts).reduce((a, b) => a + b, 0)
              return (
                <div
                  key={task.id}
                  className="glass-panel rounded-md p-3 border border-cyber-border-DEFAULT hover:border-cyber-neon-cyan/40 transition-colors cursor-pointer"
                  onClick={() => setSelectedId(task.id)}
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className={`text-[10px] font-mono ${STATUS_STYLES[task.status]}`}>
                      {t(`status.${task.status}`)}
                    </Badge>
                    <span className="font-mono text-xs text-cyber-neon-cyan font-medium">
                      {PLATFORM_LABELS[task.platform] ?? task.platform}
                    </span>
                    <span className="font-mono text-xs text-cyber-text-secondary">
                      {task.crawler_type}
                    </span>
                    {recordTotal > 0 && (
                      <span className="font-mono text-xs text-cyber-neon-green">
                        {recordTotal} {t('list.records')}
                      </span>
                    )}
                    {task.output_files.length > 0 && (
                      <span className="font-mono text-[10px] text-cyber-text-muted">
                        {formatFileSize(task.output_files.reduce((a, f) => a + f.size, 0))}
                      </span>
                    )}
                    <TaskActionButtons task={task} onOpenDialog={openDialog} />
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-[10px] font-mono text-cyber-text-muted">
                    <span>{formatDateTime(task.started_at)}</span>
                    <span>·</span>
                    <span>{formatDuration(task.started_at, task.ended_at)}</span>
                    <span>·</span>
                    <span className="truncate max-w-md">
                      {task.config.keywords || task.config.specified_ids || task.config.creator_ids || task.id}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <TaskDetailDialog
        taskId={selectedId}
        open={!!selectedId}
        onOpenChange={(o) => !o && setSelectedId(null)}
      />
      {actionDialogs}
    </div>
  )
}
