'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { StatusBadge } from '@/components/StatusBadge';
import { Target, Plus, MagnifyingGlass } from '@phosphor-icons/react';

export default function AdminMissionsPage() {
    const [missions, setMissions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await api.getMissions();
            setMissions(data);
        } catch (error) {
            console.error('Failed to load missions:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredMissions = missions.filter(m =>
        m.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.type?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading missions...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Mission Management</h3>
                    <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150">
                        <Plus size={16} weight="bold" />
                        New Mission
                    </button>
                </div>

                <div className="flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm">
                    <MagnifyingGlass className="text-slate-500" size={20} />
                    <input
                        type="text"
                        placeholder="Search missions..."
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
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Mission</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Aircraft</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Pilot</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Start Time</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {filteredMissions.map((mission) => (
                                    <tr key={mission.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{mission.title}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{mission.type}</td>
                                        <td className="px-6 py-4 font-mono text-sm">{mission.aircraft?.tailNumber || 'Unassigned'}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">
                                            {mission.pilot ? `${mission.pilot.firstName} ${mission.pilot.lastName}` : 'Unassigned'}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-sm">{new Date(mission.startTime).toLocaleString()}</td>
                                        <td className="px-6 py-4"><StatusBadge status={mission.status} /></td>
                                    </tr>
                                ))}
                                {filteredMissions.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            <Target size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
                                            No missions found
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
