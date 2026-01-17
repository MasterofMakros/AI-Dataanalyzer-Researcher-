import { useEffect, useState } from 'react';
import { Activity, CheckCircle, XCircle, AlertCircle, RefreshCw, Server } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ServiceStatus {
    name: string;
    status: 'online' | 'offline' | 'error';
    latency: number;
    code?: number;
    error?: string;
    url?: string;
}

interface SystemStatus {
    timestamp: string;
    services: ServiceStatus[];
}

const SystemMonitor = () => {
    const [status, setStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const checkStatus = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/status');
            if (!res.ok) throw new Error('Failed to fetch status');
            const data = await res.json();
            setStatus(data);
            setError(null);
        } catch (err: any) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkStatus();
        const interval = setInterval(checkStatus, 30000); // Poll every 30s
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'online': return 'text-green-500 bg-green-500/10 border-green-500/20';
            case 'offline': return 'text-red-500 bg-red-500/10 border-red-500/20';
            case 'error': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
            default: return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'online': return <CheckCircle size={18} />;
            case 'offline': return <XCircle size={18} />;
            default: return <AlertCircle size={18} />;
        }
    };

    return (
        <div className="flex flex-col space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-black dark:text-white flex items-center gap-2">
                    <Activity className="w-5 h-5 text-black/50 dark:text-white/50" />
                    System Status
                </h3>
                <button
                    onClick={checkStatus}
                    disabled={loading}
                    className="p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 disabled:opacity-50 transition-colors"
                >
                    <RefreshCw size={16} className={cn(loading && "animate-spin")} />
                </button>
            </div>

            {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm">
                    Error checking status: {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {status?.services.map((service, idx) => (
                    <div
                        key={idx}
                        className={cn(
                            "p-4 rounded-xl border flex items-center justify-between transition-all",
                            getStatusColor(service.status)
                        )}
                    >
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-white/50 dark:bg-black/20 backdrop-blur-sm">
                                <Server size={20} />
                            </div>
                            <div className="flex flex-col">
                                <span className="font-medium text-sm">{service.name}</span>
                                <span className="text-xs opacity-70 font-mono truncate max-w-[150px]">{service.url}</span>
                            </div>
                        </div>

                        <div className="flex flex-col items-end gap-1">
                            <div className="flex items-center gap-1.5 font-medium text-sm">
                                {getStatusIcon(service.status)}
                                <span className="uppercase text-xs">{service.status}</span>
                            </div>
                            {service.latency > 0 && (
                                <span className="text-xs opacity-60 font-mono">{service.latency}ms</span>
                            )}
                        </div>
                    </div>
                ))}

                {!status && loading && (
                    <div className="col-span-1 md:col-span-2 py-8 text-center text-black/40 dark:text-white/40 text-sm animate-pulse">
                        Probing services...
                    </div>
                )}
            </div>

            <div className="text-xs text-center text-black/30 dark:text-white/30 pt-4 border-t border-black/5 dark:border-white/5">
                Last updated: {status?.timestamp ? new Date(status.timestamp).toLocaleString() : 'Never'}
            </div>
        </div>
    );
};

export default SystemMonitor;
