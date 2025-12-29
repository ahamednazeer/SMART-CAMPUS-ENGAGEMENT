'use client';

import React, { useEffect, useState } from 'react';
import { Wrench, Warning, Clock, CheckCircle } from '@phosphor-icons/react';
import DashboardLayout from '@/components/DashboardLayout';
import { DataCard } from '@/components/DataCard';
import { StatusBadge } from '@/components/StatusBadge';
import { api } from '@/lib/api';
import { Aircraft } from '@/types';

export default function TechnicianDashboard() {
    const [aircraft, setAircraft] = useState<Aircraft[]>([]);
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [aircraftData, logsData] = await Promise.all([
                api.getAircraft(),
                api.getMaintenanceLogs(),
            ]);
            setAircraft(aircraftData);
            setLogs(logsData);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusUpdate = async (id: string, status: string) => {
        try {
            await api.updateAircraft(id, { status });
            loadData();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="TECHNICIAN" userName="Technician" userEmail="tech@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading...</div>
                </div>
            </DashboardLayout>
        );
    }

    const maintenanceAircraft = aircraft.filter(a => a.status === 'IN_MAINTENANCE');
    const groundedAircraft = aircraft.filter(a => a.status === 'GROUNDED');

    return (
        <DashboardLayout userRole="TECHNICIAN" userName="Technician" userEmail="tech@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Maintenance Operations</h3>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <DataCard
                        title="In Maintenance"
                        value={maintenanceAircraft.length}
                        icon={Wrench}
                    >
                        <div className="text-xs text-yellow-400 font-mono">Active work orders</div>
                    </DataCard>

                    <DataCard
                        title="Grounded"
                        value={groundedAircraft.length}
                        icon={Warning}
                    >
                        <div className="text-xs text-red-400 font-mono">Critical issues</div>
                    </DataCard>

                    <DataCard
                        title="Pending Logs"
                        value={logs.filter(l => l.status === 'PENDING').length}
                        icon={Clock}
                    >
                        <div className="text-xs text-blue-400 font-mono">Awaiting action</div>
                    </DataCard>
                </div>

                {/* Fleet Maintenance Status */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-700">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Fleet Maintenance Status</h4>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Tail Number</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Current Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {aircraft.map((craft) => (
                                    <tr key={craft.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{craft.tailNumber}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{craft.type}</td>
                                        <td className="px-6 py-4"><StatusBadge status={craft.status} /></td>
                                        <td className="px-6 py-4">
                                            <div className="flex gap-2">
                                                {craft.status !== 'READY' && (
                                                    <button
                                                        onClick={() => handleStatusUpdate(craft.id, 'READY')}
                                                        className="px-2 py-1 text-xs bg-green-950/50 text-green-400 border border-green-800 rounded-sm hover:bg-green-900/50 font-mono uppercase tracking-wider"
                                                    >
                                                        Mark Ready
                                                    </button>
                                                )}
                                                {craft.status !== 'IN_MAINTENANCE' && (
                                                    <button
                                                        onClick={() => handleStatusUpdate(craft.id, 'IN_MAINTENANCE')}
                                                        className="px-2 py-1 text-xs bg-yellow-950/50 text-yellow-400 border border-yellow-800 rounded-sm hover:bg-yellow-900/50 font-mono uppercase tracking-wider"
                                                    >
                                                        Start Maint.
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Recent Maintenance Logs */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-700">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Recent Maintenance Logs</h4>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Aircraft</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Task</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Description</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Date</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {logs.slice(0, 5).map((log) => (
                                    <tr key={log.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{log.aircraft?.tailNumber || 'N/A'}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{log.taskType}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{log.description}</td>
                                        <td className="px-6 py-4"><StatusBadge status={log.status} /></td>
                                        <td className="px-6 py-4 font-mono text-sm">{new Date(log.createdAt).toLocaleDateString()}</td>
                                    </tr>
                                ))}
                                {logs.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            No maintenance logs found
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
