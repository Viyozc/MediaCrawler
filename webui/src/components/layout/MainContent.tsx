import { useTranslation } from 'react-i18next'
import { Terminal } from '@/components/console/Terminal'
import { TaskHistoryList } from '@/components/tasks/TaskHistoryList'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { useLogWebSocket } from '@/hooks/useWebSocket'

export function MainContent() {
  // Connect to WebSocket for logs
  useLogWebSocket()
  const { t } = useTranslation('tasks')

  return (
    <main className="flex-1 flex flex-col overflow-hidden min-h-0 relative z-10 gap-2">
      <Tabs defaultValue="history" className="h-full flex flex-col gap-2">
        <TabsList className="flex-shrink-0">
          <TabsTrigger value="console" className="font-mono text-xs">Console</TabsTrigger>
          <TabsTrigger value="history" className="font-mono text-xs">{t('title')}</TabsTrigger>
        </TabsList>
        <TabsContent value="console" className="flex-1 overflow-hidden mt-0">
          <Terminal />
        </TabsContent>
        <TabsContent value="history" className="flex-1 overflow-hidden mt-0">
          <TaskHistoryList />
        </TabsContent>
      </Tabs>
    </main>
  )
}
