'use client';

import React, { useEffect, useState } from 'react';
import {
    Wrench,
    Warning,
    CheckCircle,
    TrendUp,
    Airplane,
    Clock,
    CalendarCheck,
    ArrowRight
} from '@phosphor-icons/react';
import api from '@/lib/api';
import { toast } from 'sonner';

interface AircraftPrediction {
    id: string;
    tailNumber: string;
    model: string;
    flightHours: number;
    lastMaintenance: string | null;
    predictiveStatus: 'CRITICAL' | 'WARNING' | 'HEALTHY';
    daysSinceLastMaintenance: number;
    maintenanceReasons: string[];
}

export default function PredictiveMaintenancePage() {
    const [data, setData] = useState<AircraftPrediction[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const response = await api.get('/maintenance/predictive');
            setData(response.data);
        } catch (error) {
            console.error('Failed to fetch predictive maintenance data:', error);
            toast.error('Failed to load predictive maintenance data');
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'CRITICAL': return 'text-red-400 bg-red-950/30 border-red-900/50';
            case 'WARNING': return 'text-amber-400 bg-amber-950/30 border-amber-900/50';
            case 'HEALTHY': return 'text-emerald-400 bg-emerald-950/30 border-emerald-900/50';
            default: return 'text-slate-400 bg-slate-900 border-slate-800';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'CRITICAL': return <Warning weight="fill" className="text-red-400" />;
            case 'WARNING': return <TrendUp weight="bold" className="text-amber-400" />;
            case 'HEALTHY': return <CheckCircle weight="fill" className="text-emerald-400" />;
            default: return <Wrench />;
        }
    };

    const stats = {
        critical: data.filter(d => d.predictiveStatus === 'CRITICAL').length,
        warning: data.filter(d => d.predictiveStatus === 'WARNING').length,
        healthy: data.filter(d => d.predictiveStatus === 'HEALTHY').length,
    };

    if (loading) {
        return <div className="p-8 text-center text-slate-400 font-mono animate-pulse">Analyzing fleet telemetry...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-100 font-chivo uppercase tracking-wide">Predictive Maintenance</h1>
                    <p className="text-slate-400 text-sm font-mono mt-1">AI-driven fleet health analysis & forecasting</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={fetchData} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono uppercase tracking-wider rounded-sm border border-slate-700 transition-colors">
                        Refresh Analysis
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-900/50 border border-red-900/30 p-4 rounded-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Warning size={64} />
                    </div>
                    <div className="relative z-10">
                        <p className="text-red-400 text-xs font-mono uppercase tracking-wider mb-1">Critical Attention</p>
                        <h3 className="text-3xl font-bold text-slate-100 font-chivo">{stats.critical}</h3>
                        <p className="text-slate-500 text-xs mt-2">Aircraft requiring immediate service</p>
                    </div>
                    <div className="absolute bottom-0 left-0 w-full h-1 bg-red-500/20">
                        <div className="h-full bg-red-500" style={{ width: `${(stats.critical / data.length) * 100}%` }} />
                    </div>
                </div>

                <div className="bg-slate-900/50 border border-amber-900/30 p-4 rounded-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <TrendUp size={64} />
                    </div>
                    <div className="relative z-10">
                        <p className="text-amber-400 text-xs font-mono uppercase tracking-wider mb-1">Approaching Limits</p>
                        <h3 className="text-3xl font-bold text-slate-100 font-chivo">{stats.warning}</h3>
                        <p className="text-slate-500 text-xs mt-2">Maintenance due soon</p>
                    </div>
                    <div className="absolute bottom-0 left-0 w-full h-1 bg-amber-500/20">
                        <div className="h-full bg-amber-500" style={{ width: `${(stats.warning / data.length) * 100}%` }} />
                    </div>
                </div>

                <div className="bg-slate-900/50 border border-emerald-900/30 p-4 rounded-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <CheckCircle size={64} />
                    </div>
                    <div className="relative z-10">
                        <p className="text-emerald-400 text-xs font-mono uppercase tracking-wider mb-1">Fleet Health</p>
                        <h3 className="text-3xl font-bold text-slate-100 font-chivo">{stats.healthy}</h3>
                        <p className="text-slate-500 text-xs mt-2">Aircraft in good standing</p>
                    </div>
                    <div className="absolute bottom-0 left-0 w-full h-1 bg-emerald-500/20">
                        <div className="h-full bg-emerald-500" style={{ width: `${(stats.healthy / data.length) * 100}%` }} />
                    </div>
                </div>
            </div>

            {/* Main List */}
            <div className="bg-slate-900 border border-slate-800 rounded-sm overflow-hidden">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
                    <h3 className="font-chivo font-bold text-sm uppercase tracking-wider text-slate-300">Fleet Analysis</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-800 bg-slate-950/50 text-xs uppercase tracking-wider text-slate-500 font-mono">
                                <th className="p-4 font-medium">Status</th>
                                <th className="p-4 font-medium">Aircraft</th>
                                <th className="p-4 font-medium">Flight Hours</th>
                                <th className="p-4 font-medium">Last Maint.</th>
                                <th className="p-4 font-medium">Analysis</th>
                                <th className="p-4 font-medium text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {data.map((item) => (
                                <tr key={item.id} className="group hover:bg-slate-800/50 transition-colors">
                                    <td className="p-4">
                                        <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusColor(item.predictiveStatus)}`}>
                                            {getStatusIcon(item.predictiveStatus)}
                                            {item.predictiveStatus}
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center text-slate-400">
                                                <Airplane weight="duotone" />
                                            </div>
                                            <div>
                                                <div className="font-bold text-slate-200 font-mono">{item.tailNumber}</div>
                                                <div className="text-xs text-slate-500">{item.model}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2 text-slate-300 font-mono text-sm">
                                            <Clock size={16} className="text-slate-500" />
                                            {item.flightHours.toFixed(1)} hrs
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2 text-slate-300 font-mono text-sm">
                                            <CalendarCheck size={16} className="text-slate-500" />
                                            {item.lastMaintenance ? new Date(item.lastMaintenance).toLocaleDateString() : 'Never'}
                                            <span className="text-xs text-slate-500">({item.daysSinceLastMaintenance} days ago)</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        {item.maintenanceReasons.length > 0 ? (
                                            <ul className="space-y-1">
                                                {item.maintenanceReasons.map((reason, idx) => (
                                                    <li key={idx} className="text-xs text-amber-400 flex items-start gap-1.5">
                                                        <span className="mt-0.5">•</span>
                                                        {reason}
                                                    </li>
                                                ))}
                                            </ul>
                                        ) : (
                                            <span className="text-xs text-emerald-500 flex items-center gap-1">
                                                <CheckCircle size={12} weight="fill" />
                                                All systems nominal
                                            </span>
                                        )}
                                    </td>
                                    <td className="p-4 text-right">
                                        <button className="text-blue-400 hover:text-blue-300 text-xs font-medium uppercase tracking-wider flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            Schedule
                                            <ArrowRight />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
