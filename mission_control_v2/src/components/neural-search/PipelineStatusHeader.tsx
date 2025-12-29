import { PipelineStatus } from '@/types/neural-search';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface PipelineStatusHeaderProps {
  status: PipelineStatus;
  currentTime: Date;
}

export function PipelineStatusHeader({ status, currentTime }: PipelineStatusHeaderProps) {
  const formatLastSync = (date: Date) => {
    const diff = Math.floor((currentTime.getTime() - date.getTime()) / 1000);
    if (diff < 60) return `vor ${diff}s`;
    if (diff < 3600) return `vor ${Math.floor(diff / 60)} Min`;
    return `vor ${Math.floor(diff / 3600)}h`;
  };

  const gpuStatusColor = {
    online: 'bg-emerald-500',
    busy: 'bg-amber-500',
    offline: 'bg-rose-500',
  };

  return (
    <TooltipProvider>
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900/80 border-b border-slate-800 backdrop-blur-sm">
        {/* Left: Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center">
              <BrainIcon className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold text-slate-100 tracking-tight">Neural Search</span>
          </div>
        </div>

        {/* Center: Status Pills */}
        <div className="hidden md:flex items-center gap-3">
          {/* GPU Status */}
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <span className={`w-2 h-2 rounded-full ${gpuStatusColor[status.gpuStatus]} animate-pulse`} />
                <span className="text-xs font-medium text-slate-300">GPU</span>
                <span className="text-xs text-slate-500">{status.gpuModel}</span>
                <Badge variant="outline" className="text-[10px] border-slate-600 text-slate-400 px-1.5 py-0">
                  {status.vramUsage}% VRAM
                </Badge>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>GPU Status: {status.gpuStatus}</p>
            </TooltipContent>
          </Tooltip>

          {/* Workers */}
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <span className={`w-2 h-2 rounded-full ${
                  status.workersActive === status.workersTotal ? 'bg-emerald-500' : 'bg-amber-500'
                }`} />
                <span className="text-xs font-medium text-slate-300">Workers</span>
                <span className="text-xs text-slate-400">
                  {status.workersActive}/{status.workersTotal}
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{status.workersActive} von {status.workersTotal} Workern aktiv</p>
            </TooltipContent>
          </Tooltip>

          {/* Queue */}
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <QueueIcon className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-xs font-medium text-slate-300">Queue</span>
                <Badge
                  variant="outline"
                  className={`text-[10px] px-1.5 py-0 ${
                    status.queueDepth > 50
                      ? 'border-amber-600 text-amber-400'
                      : 'border-slate-600 text-slate-400'
                  }`}
                >
                  {status.queueDepth}
                </Badge>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{status.queueDepth} Jobs in der Warteschlange</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Right: Time & Index Info */}
        <div className="flex items-center gap-4">
          {/* Index Info */}
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
            <DatabaseIcon className="w-3.5 h-3.5" />
            <span>{status.indexedDocuments.toLocaleString()} Docs</span>
            <span className="text-slate-700">•</span>
            <span>Sync {formatLastSync(status.lastSync)}</span>
          </div>

          {/* Time */}
          <div className="text-lg font-mono text-slate-300">
            {currentTime.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>

      {/* Mobile Status Bar */}
      <div className="md:hidden flex items-center justify-between px-4 py-1.5 bg-slate-800/50 border-b border-slate-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${gpuStatusColor[status.gpuStatus]}`} />
            <span className="text-slate-400">GPU</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">{status.workersActive}W</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Q:{status.queueDepth}</span>
          </div>
        </div>
        <span className="text-slate-500">{status.indexedDocuments.toLocaleString()} Docs</span>
      </div>
    </TooltipProvider>
  );
}

// Icons
function BrainIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2a9 9 0 0 0-9 9c0 4.17 2.84 7.67 6.69 8.69L12 22l2.31-2.31C18.16 18.67 21 15.17 21 11a9 9 0 0 0-9-9zm0 16c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z" />
    </svg>
  );
}

function QueueIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  );
}

function DatabaseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  );
}
