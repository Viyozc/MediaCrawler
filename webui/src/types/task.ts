export type TaskStatus = 'running' | 'completed' | 'failed' | 'stopped'

export interface TaskConfigSnapshot {
  platform: string
  login_type: string
  crawler_type: string
  keywords: string
  specified_ids: string
  creator_ids: string
  start_page: number
  enable_comments: boolean
  enable_sub_comments: boolean
  save_option: string
  cookies: string
  headless: boolean
  max_notes_count: number | null
  max_comments_count: number | null
}

export interface OutputFile {
  path: string
  size: number
  record_count: number | null
  file_type: string
}

export interface TaskRecord {
  id: string
  status: TaskStatus
  platform: string
  crawler_type: string
  config: TaskConfigSnapshot
  started_at: string
  ended_at: string | null
  exit_code: number | null
  output_files: OutputFile[]
  record_counts: Record<string, number>
  log_path: string | null
  error: string | null
}

export interface TaskListResponse {
  tasks: TaskRecord[]
  total: number
}

export interface TaskListParams {
  status?: TaskStatus
  platform?: string
  page?: number
  page_size?: number
}
