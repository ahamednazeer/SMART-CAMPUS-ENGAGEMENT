'use client';

import React from 'react';
import { Warning, X, Siren, Bell, Info } from '@phosphor-icons/react';
import { Notification, Emergency } from '@/types';

interface AlertsBannerProps {
    alerts: Notification[];
    emergencies: Emergency[];
    onDismiss?: (alertId: string) => void;
}

const alertTypeConfig = {
    EMERGENCY: { color: 'bg-red-500/20 border-red-500/50 text-red-400', icon: Siren },
    WARNING: { color: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400', icon: Warning },
    INFO: { color: 'bg-blue-500/20 border-blue-500/50 text-blue-400', icon: Info },
    SUCCESS: { color: 'bg-green-500/20 border-green-500/50 text-green-400', icon: Bell },
};

const severityColors: Record<string, string> = {
    CRITICAL: 'bg-red-600/30 border-red-500',
    HIGH: 'bg-red-500/20 border-red-500/60',
    MEDIUM: 'bg-yellow-500/20 border-yellow-500/60',
    LOW: 'bg-blue-500/20 border-blue-500/60',
};

export default function AlertsBanner({ alerts, emergencies, onDismiss }: AlertsBannerProps) {
    const hasAlerts = alerts.length > 0 || emergencies.length > 0;

    if (!hasAlerts) {
        return null;
    }

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const mins = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);

        if (mins < 60) return `${mins}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    return (
        <div className="space-y-2">
            {/* Active Emergencies (highest priority) */}
            {emergencies.map((emergency) => (
                <div
                    key={emergency.id}
                    className={`flex items-center gap-3 px-4 py-3 rounded-sm border ${severityColors[emergency.severity] || severityColors.MEDIUM}`}
                >
                    <div className="animate-pulse">
                        <Siren size={20} weight="fill" className="text-red-400" />
                    </div>
                    <div className="flex-1">
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-red-300 uppercase tracking-wider">
                                {emergency.type.replace('_', ' ')}
                            </span>
                            <span className="text-xs text-slate-500">•</span>
                            <span className="text-xs text-slate-400 font-mono">
                                {formatTime(emergency.createdAt)}
                            </span>
                        </div>
                        <div className="font-medium text-white text-sm">
                            {emergency.title}
                        </div>
                        {emergency.location && (
                            <div className="text-xs text-slate-400">
                                {emergency.location}
                            </div>
                        )}
                    </div>
                    <div className="px-2 py-0.5 bg-red-600/40 border border-red-500 rounded text-xs font-mono text-red-300 uppercase">
                        {emergency.severity}
                    </div>
                </div>
            ))}

            {/* Notifications */}
            {alerts.map((alert) => {
                const config = alertTypeConfig[alert.type] || alertTypeConfig.INFO;
                const Icon = config.icon;

                return (
                    <div
                        key={alert.id}
                        className={`flex items-center gap-3 px-4 py-2.5 rounded-sm border ${config.color}`}
                    >
                        <Icon size={18} weight="fill" />
                        <div className="flex-1">
                            <div className="font-medium text-sm">{alert.title}</div>
                            <div className="text-xs text-slate-400">{alert.message}</div>
                        </div>
                        <span className="text-xs text-slate-500 font-mono">
                            {formatTime(alert.createdAt)}
                        </span>
                        {onDismiss && (
                            <button
                                onClick={() => onDismiss(alert.id)}
                                className="p-1 hover:bg-slate-700/50 rounded transition-colors"
                            >
                                <X size={14} className="text-slate-400" />
                            </button>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
