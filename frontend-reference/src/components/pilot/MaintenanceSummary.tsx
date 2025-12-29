'use client';

import React from 'react';
import { Wrench, User, Clock, CheckCircle, Warning, Spinner } from '@phosphor-icons/react';
import { MaintenanceLog } from '@/types';

interface MaintenanceSummaryProps {
    logs: MaintenanceLog[];
}

const statusConfig = {
    PENDING: { color: 'text-yellow-400', icon: Clock },
    IN_PROGRESS: { color: 'text-blue-400', icon: Spinner },
    COMPLETED: { color: 'text-green-400', icon: CheckCircle },
    CANCELLED: { color: 'text-slate-400', icon: Warning },
};

export default function MaintenanceSummary({ logs }: MaintenanceSummaryProps) {
    if (!logs || logs.length === 0) {
        return (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4">
                <div className="flex items-center gap-2 mb-3">
                    <Wrench size={18} weight="duotone" className="text-blue-400" />
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Recent Maintenance</h4>
                </div>
                <div className="text-center text-slate-500 font-mono text-sm py-4">
                    No recent maintenance records
                </div>
            </div>
        );
    }

    const formatDate = (dateString?: string) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4">
            <div className="flex items-center gap-2 mb-3">
                <Wrench size={18} weight="duotone" className="text-blue-400" />
                <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Recent Maintenance</h4>
            </div>
            <div className="space-y-3">
                {logs.slice(0, 3).map((log) => {
                    const config = statusConfig[log.status] || statusConfig.PENDING;
                    const StatusIcon = config.icon;

                    return (
                        <div
                            key={log.id}
                            className="bg-slate-900/40 border border-slate-700/40 rounded-sm p-3"
                        >
                            <div className="flex items-start justify-between mb-1">
                                <div className="font-medium text-sm text-white truncate flex-1">
                                    {log.taskType}
                                </div>
                                <div className={`flex items-center gap-1 ${config.color}`}>
                                    <StatusIcon size={12} weight="fill" />
                                    <span className="text-xs font-mono uppercase">{log.status}</span>
                                </div>
                            </div>
                            <div className="text-xs text-slate-400 line-clamp-1 mb-2">
                                {log.description}
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                                {log.technician && (
                                    <div className="flex items-center gap-1">
                                        <User size={10} />
                                        <span className="font-mono">
                                            {log.technician.firstName} {log.technician.lastName}
                                        </span>
                                    </div>
                                )}
                                <div className="flex items-center gap-1">
                                    <Clock size={10} />
                                    <span className="font-mono">
                                        {formatDate(log.createdAt || log.startedAt)}
                                    </span>
                                </div>
                            </div>
                            {log.priority && log.priority !== 'MEDIUM' && (
                                <div className={`mt-2 inline-flex px-1.5 py-0.5 text-xs font-mono rounded ${log.priority === 'HIGH' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'
                                    }`}>
                                    {log.priority}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
