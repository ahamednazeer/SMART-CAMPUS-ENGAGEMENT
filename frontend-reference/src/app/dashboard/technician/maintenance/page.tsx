'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { StatusBadge } from '@/components/StatusBadge';
import { Wrench, Plus, MagnifyingGlass } from '@phosphor-icons/react';

export default function TechnicianMaintenancePage() {
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await api.getMaintenanceLogs();
            setLogs(data);
        } catch (error) {
            console.error('Failed to load maintenance logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredLogs = logs.filter(log =>
        log.aircraft?.tailNumber?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.taskType?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <DashboardLayout userRole="TECHNICIAN" userName="Technician" userEmail="tech@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading maintenance logs...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="TECHNICIAN" userName="Technician" userEmail="tech@airbase.mil">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Maintenance Logs</h3>
                    <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150">
                        <Plus size={16} weight="bold" />
                        New Log
                    </button>
                </div>

                <div className="flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm">
                    <MagnifyingGlass className="text-slate-500" size={20} />
                    <input
                        type="text"
                        placeholder="Search maintenance logs..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-transparent border-none focus:outline-none text-slate-200 w-full placeholder-slate-500 font-mono text-sm"
                    />
                </div>

                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Aircraft</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Task Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Description</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Date</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {filteredLogs.map((log) => (
                                    <tr key={log.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{log.aircraft?.tailNumber || 'N/A'}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{log.taskType}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{log.description}</td>
                                        <td className="px-6 py-4"><StatusBadge status={log.status} /></td>
                                        <td className="px-6 py-4 font-mono text-sm">{new Date(log.createdAt).toLocaleDateString()}</td>
                                    </tr>
                                ))}
                                {filteredLogs.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            <Wrench size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
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
