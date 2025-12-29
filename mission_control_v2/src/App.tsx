import { useEffect, useState, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { NeuralSearchPage } from '@/components/neural-search'

interface ComponentStatus {
  name: string
  status: string
  cpu?: number
  memory?: number
}

interface Job {
  id: string
  type: string
  payload?: { path?: string }
  status: string
  progress?: number
  created_at?: string
  estimated_ms?: number
  result?: { actualMs?: number }
}

interface SystemStatus {
  worker: string
  queue_depth: { interactive: number; batch: number }
  components: ComponentStatus[]
  jobs: Job[]
}

// Refined System Node
const SystemNode = ({
  icon, label, sublabel, status
}: {
  icon: React.ReactNode
  label: string
  sublabel: string
  status: 'online' | 'offline' | 'busy' | 'idle'
}) => {
  const styles = {
    online: { ring: 'ring-emerald-600/50', bg: 'bg-emerald-900/30', dot: 'bg-emerald-500' },
    idle: { ring: 'ring-teal-600/50', bg: 'bg-teal-900/30', dot: 'bg-teal-500' },
    busy: { ring: 'ring-amber-600/50', bg: 'bg-amber-900/30', dot: 'bg-amber-500' },
    offline: { ring: 'ring-rose-600/50', bg: 'bg-rose-900/30', dot: 'bg-rose-500' },
  }
  const s = styles[status]

  return (
    <div className="flex flex-col items-center">
      <div className={`relative w - 16 h - 16 md: w - 20 md: h - 20 rounded - xl ${s.bg} ring - 1 ${s.ring} flex items - center justify - center transition - all duration - 300 hover: scale - 105`}>
        <div className="text-slate-300 w-8 h-8 md:w-10 md:h-10">{icon}</div>
        <div className={`absolute - bottom - 0.5 - right - 0.5 w - 3 h - 3 rounded - full ${s.dot} ring - 2 ring - background`} />
      </div>
      <span className="mt-2 text-xs font-medium text-slate-300">{label}</span>
      <span className={`text - [10px] font - medium ${status === 'offline' ? 'text-rose-400' : status === 'busy' ? 'text-amber-400' : 'text-teal-400'} `}>
        {sublabel}
      </span>
    </div>
  )
}

// Refined Data Flow Arrow
const DataFlowArrow = ({ active }: { active: boolean }) => (
  <div className="relative flex items-center mx-3 md:mx-5">
    <div className={`w - 10 md: w - 16 h - px ${active ? 'bg-teal-700' : 'bg-slate-700'} relative overflow - hidden`}>
      {active && (
        <>
          <div className="absolute top-1/2 -translate-y-1/2 w-2 h-2 bg-teal-500/80 rounded-full animate-flow-right" />
          <div className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-teal-400/60 rounded-full animate-flow-right-delayed" />
        </>
      )}
    </div>
    <div className={`w - 0 h - 0 border - t - [4px] border - b - [4px] border - l - [6px] ${active ? 'border-l-teal-600' : 'border-l-slate-600'} border - t - transparent border - b - transparent`} />
  </div>
)

// Job Card
const JobCard = ({ job, formatTime }: { job: Job; formatTime: (ms?: number) => string }) => {
  const statusStyles: Record<string, string> = {
    done: 'border-emerald-700/40 bg-emerald-950/20',
    processing: 'border-amber-700/40 bg-amber-950/20',
    queued: 'border-slate-600/40 bg-slate-800/20',
    failed: 'border-rose-700/40 bg-rose-950/20',
  }

  const progress = job.progress ?? (job.status === 'done' ? 100 : job.status === 'queued' ? 0 : 50)
  const barColor = job.status === 'done' ? 'bg-emerald-600' : job.status === 'processing' ? 'bg-amber-600' : 'bg-slate-600'

  return (
    <div className={`p - 3 rounded - lg border ${statusStyles[job.status] || 'border-slate-700/40'} transition - all duration - 200`}>
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-teal-400">{job.id}</span>
          <Badge variant="outline" className="text-[10px] border-slate-600 text-slate-400">{job.type}</Badge>
        </div>
        <Badge className={`text - [10px] ${job.status === 'done' ? 'bg-emerald-700' : job.status === 'processing' ? 'bg-amber-700' : job.status === 'failed' ? 'bg-rose-700' : 'bg-slate-600'} `}>
          {job.status}
        </Badge>
      </div>
      <div className="text-[11px] text-slate-500 font-mono truncate mb-2">{job.payload?.path || '—'}</div>
      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h - full ${barColor} transition - all duration - 500 rounded - full`} style={{ width: `${progress}% ` }}>
          {job.status === 'processing' && <div className="h-full bg-white/20 animate-shimmer" />}
        </div>
      </div>
      <div className="flex justify-between text-[10px] text-slate-500 mt-1.5">
        <span>{progress}%</span>
        <span>Est: {formatTime(job.estimated_ms)} | Act: {formatTime(job.result?.actualMs)}</span>
      </div>
    </div>
  )
}

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [time, setTime] = useState(new Date())
  const [logs, setLogs] = useState<string[]>(['[SYS] Dashboard initialized'])
  const [isConnected, setIsConnected] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)

  const addLog = (msg: string) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg} `, ...prev.slice(0, 99)])
  const copyLogs = async () => { await navigator.clipboard.writeText(logs.join('\n')); addLog('Logs copied') }

  const sendWorkerCommand = async (cmd: string) => {
    try {
      const res = await fetch('/api/worker/command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: cmd }) })
      const data = await res.json()
      addLog(`CMD ${cmd}: ${data.status} `)
    } catch (e) { addLog(`ERR: ${e} `) }
  }

  const submitTestJob = async () => {
    try {
      const res = await fetch('/api/job/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'transcribe', payload: { path: 'F:/12 Datenpool Mediathek/sample.mp4' }, priority: 10 }) })
      const data = await res.json()
      addLog(`Job ${data.id} submitted`)
    } catch (e) { addLog(`ERR: ${e} `) }
  }

  const clearQueue = async () => {
    try {
      const res = await fetch('/api/queue/clear?queue=batch', { method: 'DELETE' })
      const data = await res.json()
      addLog(`Queue cleared: ${data.jobs_removed} `)
    } catch (e) { addLog(`ERR: ${e} `) }
  }

  useEffect(() => { const t = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(t) }, [])

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/status/system')
        if (!res.ok) throw new Error()
        setStatus(await res.json())
        setIsConnected(true)
      } catch { setStatus(null); setIsConnected(false) }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const getWorkerStatus = (): 'online' | 'offline' | 'busy' | 'idle' => {
    if (!status) return 'offline'
    if (status.worker === 'BUSY') return 'busy'
    if (status.worker === 'IDLE') return 'idle'
    if (status.worker.includes('PAUSED')) return 'busy'
    return 'offline'
  }

  const formatTime = (ms?: number) => { if (!ms) return '—'; const s = Math.floor(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')} ` }

  const workerStatus = getWorkerStatus()
  const isActive = workerStatus !== 'offline'

  // SVG Icons
  const FolderIcon = <svg fill="currentColor" viewBox="0 0 24 24"><path d="M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2z" /></svg>
  const ServerIcon = <svg fill="currentColor" viewBox="0 0 24 24"><path d="M20 13H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1v-6c0-.55-.45-1-1-1zM7 19c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zM20 3H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1V4c0-.55-.45-1-1-1zM7 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z" /></svg>
  const ComputerIcon = <svg fill="currentColor" viewBox="0 0 24 24"><path d="M20 18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z" /></svg>
  const BrainIcon = <svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 2a9 9 0 0 0-9 9c0 4.17 2.84 7.67 6.69 8.69L12 22l2.31-2.31C18.16 18.67 21 15.17 21 11a9 9 0 0 0-9-9zm0 16c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z" /></svg>

  return (
    <div className="min-h-screen bg-[hsl(210,20%,6%)] p-4 md:p-6 text-slate-200">
      {/* Header */}
      <header className="flex justify-between items-center mb-6 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-slate-100">CONDUCTOR</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-slate-500">Hybrid AI Orchestration</span>
            <div className={`flex items - center gap - 1 px - 1.5 py - 0.5 rounded text - [10px] ${isConnected ? 'bg-teal-900/40 text-teal-400' : 'bg-rose-900/40 text-rose-400'} `}>
              <span className={`w - 1.5 h - 1.5 rounded - full ${isConnected ? 'bg-teal-500' : 'bg-rose-500'} `} />
              {isConnected ? 'Connected' : 'Offline'}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xl md:text-2xl font-mono text-slate-300">{time.toLocaleTimeString()}</div>
          <div className="text-[10px] text-slate-600 uppercase tracking-wider">System Time</div>
        </div>
      </header>

      <Tabs defaultValue="search" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 bg-slate-800/50 h-9">
          <TabsTrigger value="search" className="text-xs data-[state=active]:bg-teal-700">Search</TabsTrigger>
          <TabsTrigger value="overview" className="text-xs data-[state=active]:bg-slate-700">Overview</TabsTrigger>
          <TabsTrigger value="jobs" className="text-xs data-[state=active]:bg-slate-700">Jobs ({status?.jobs?.length || 0})</TabsTrigger>
          <TabsTrigger value="system" className="text-xs data-[state=active]:bg-slate-700">System</TabsTrigger>
        </TabsList>

        {/* SEARCH - Neural Search Interface */}
        <TabsContent value="search" className="h-[calc(100vh-220px)]">
          <NeuralSearchPage />
        </TabsContent>

        {/* OVERVIEW */}
        <TabsContent value="overview" className="space-y-4">
          {/* Architecture */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">System Architecture</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center py-6 overflow-x-auto">
                <SystemNode icon={FolderIcon} label="F: Drive" sublabel="7.2 TB" status="online" />
                <DataFlowArrow active={isActive} />
                <SystemNode icon={ServerIcon} label="Conductor" sublabel={isConnected ? 'Active' : 'Offline'} status={isConnected ? 'online' : 'offline'} />
                <DataFlowArrow active={isActive} />
                <SystemNode icon={ComputerIcon} label="RTX 5090" sublabel={status?.worker || 'Offline'} status={workerStatus} />
                <DataFlowArrow active={workerStatus === 'busy'} />
                <SystemNode icon={BrainIcon} label="ChromaDB" sublabel="RAG" status={isActive ? 'idle' : 'offline'} />
              </div>
            </CardContent>
          </Card>

          {/* Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Worker */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">Worker</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <div className={`text - 3xl font - semibold mb - 3 ${workerStatus === 'offline' ? 'text-rose-400' : workerStatus === 'busy' ? 'text-amber-400' : 'text-teal-400'} `}>
                  {status?.worker || 'OFFLINE'}
                </div>
                <div className="flex justify-center gap-2">
                  <Button size="sm" variant="outline" className="text-xs border-slate-700 hover:bg-slate-800" onClick={() => sendWorkerCommand('start')}>Start</Button>
                  <Button size="sm" variant="outline" className="text-xs border-slate-700 hover:bg-slate-800" onClick={() => sendWorkerCommand('pause')}>Pause</Button>
                  <Button size="sm" variant="outline" className="text-xs border-slate-700 hover:bg-slate-800 text-rose-400 hover:text-rose-300" onClick={() => sendWorkerCommand('stop')}>Stop</Button>
                </div>
              </CardContent>
            </Card>

            {/* Queues */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">Queues</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between items-center p-2 rounded bg-slate-800/50">
                  <span className="text-xs text-slate-400">Interactive</span>
                  <span className="text-lg font-mono text-teal-400">{status?.queue_depth.interactive ?? 0}</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded bg-slate-800/50">
                  <span className="text-xs text-slate-400">Batch</span>
                  <span className="text-lg font-mono text-slate-300">{status?.queue_depth.batch ?? 0}</span>
                </div>
                <div className="flex gap-2 pt-1">
                  <Button size="sm" className="flex-1 text-xs bg-teal-700 hover:bg-teal-600" onClick={submitTestJob}>+ Job</Button>
                  <Button size="sm" variant="outline" className="flex-1 text-xs border-slate-700" onClick={clearQueue}>Clear</Button>
                </div>
              </CardContent>
            </Card>

            {/* Components */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">Components</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {(status?.components || []).map((c, i) => (
                  <div key={i} className="flex justify-between items-center p-2 rounded bg-slate-800/50 text-xs">
                    <span className="text-slate-400">{c.name}</span>
                    <Badge className={`text - [10px] ${c.status === 'online' ? 'bg-emerald-800 text-emerald-300' : 'bg-rose-800 text-rose-300'} `}>
                      {c.status === 'online' && c.cpu !== undefined ? `${c.cpu}% ` : c.status}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* JOBS */}
        <TabsContent value="jobs">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2 flex flex-row justify-between items-center">
              <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">Job Pipeline</CardTitle>
              <Button size="sm" className="text-xs bg-teal-700 hover:bg-teal-600" onClick={submitTestJob}>+ Add Job</Button>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-80">
                <div className="space-y-2">
                  {(status?.jobs || []).map(job => <JobCard key={job.id} job={job} formatTime={formatTime} />)}
                  {(!status?.jobs || status.jobs.length === 0) && (
                    <div className="text-center text-slate-500 py-12">
                      <div className="text-3xl mb-2 opacity-50">✓</div>
                      <div className="text-sm">Queue empty</div>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SYSTEM */}
        <TabsContent value="system">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2 flex flex-row justify-between items-center">
              <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">System Logs</CardTitle>
              <div className="flex gap-1.5">
                <Button size="sm" variant="outline" className="text-xs h-7 border-slate-700" onClick={() => setLogs([])}>Clear</Button>
                <Button size="sm" variant="outline" className="text-xs h-7 border-slate-700" onClick={copyLogs}>Copy</Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-72 bg-slate-950 rounded-lg p-3 font-mono text-xs">
                <div ref={logRef} className="space-y-0.5">
                  {logs.map((log, i) => (
                    <div key={i} className={`${log.includes('ERR') ? 'text-rose-400' : log.includes('CMD') ? 'text-amber-400' : 'text-slate-500'} `}>{log}</div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer */}
      <div className="mt-4 px-3 py-2 bg-slate-900/50 rounded-lg border border-slate-800 font-mono text-[10px] text-slate-500 flex justify-between items-center">
        <span className="truncate">{logs[0]}</span>
        <Button size="sm" variant="ghost" className="h-5 text-[10px] text-slate-500 hover:text-slate-300" onClick={copyLogs}>📋</Button>
      </div>
    </div>
  )
}

export default App
