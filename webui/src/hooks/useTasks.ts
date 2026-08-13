import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { taskApi } from '@/lib/api'
import type { TaskListParams } from '@/types/task'

export function useTaskList(params: TaskListParams = {}) {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: async () => {
      const { data } = await taskApi.list(params)
      return data
    },
    refetchInterval: (query) => {
      // Poll while any task is running
      const tasks = query.state.data?.tasks ?? []
      return tasks.some((t) => t.status === 'running') ? 3000 : false
    },
  })
}

export function useTask(taskId: string | null) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const { data } = await taskApi.get(taskId!)
      return data
    },
    enabled: !!taskId,
  })
}

export function useTaskLogs(taskId: string | null) {
  return useQuery({
    queryKey: ['taskLogs', taskId],
    queryFn: async () => {
      const { data } = await taskApi.getLogs(taskId!)
      return data.logs
    },
    enabled: !!taskId,
  })
}

export function useDeleteTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: string) => taskApi.delete(taskId),
    onSuccess: () => {
      toast.success('Task deleted')
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete task: ${error.message}`)
    },
  })
}
