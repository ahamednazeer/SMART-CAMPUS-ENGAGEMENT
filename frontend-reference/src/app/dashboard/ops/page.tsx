'use client';

import React, { useEffect, useState } from 'react';
import { Calendar, Airplane, Target, Plus, ArrowsClockwise } from '@phosphor-icons/react';
import DashboardLayout from '@/components/DashboardLayout';
import { DataCard } from '@/components/DataCard';
import { StatusBadge } from '@/components/StatusBadge';
import { api } from '@/lib/api';
import CreateMissionModal from '@/components/CreateMissionModal';

export default function OpsDashboard() {
    const [missions, setMissions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const missionsData = await api.getMissions();
            setMissions(missionsData);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="OPS_OFFICER" userName="Ops Officer" userEmail="ops@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading...</div>
                </div>
            </DashboardLayout>
        );
    }

    const plannedMissions = missions.filter(m => m.status === 'PLANNED');
    const activeMissions = missions.filter(m => m.status === 'IN_PROGRESS');

    return (
        <DashboardLayout userRole="OPS_OFFICER" userName="Ops Officer" userEmail="ops@airbase.mil">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Mission Planning</h3>
                    <div className="flex gap-3">
                        <button
                            onClick={loadData}
                            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 transition-all duration-150"
                        >
                            <ArrowsClockwise size={16} weight="bold" />
                            Refresh
                        </button>
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150"
                        >
                            <Plus size={16} weight="bold" />
                            New Mission
                        </button>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <DataCard
                        title="Planned Missions"
                        value={plannedMissions.length}
                        icon={Calendar}
                    >
                        <div className="text-xs text-blue-400 font-mono">Upcoming flights</div>
                    </DataCard>

                    <DataCard
                        title="Active Missions"
                        value={activeMissions.length}
                        icon={Airplane}
                    >
                        <div className="text-xs text-green-400 font-mono">Currently in air</div>
                    </DataCard>

                    <DataCard
                        title="Total Missions Today"
                        value={missions.length}
                        icon={Target}
                    >
                        <div className="text-xs text-slate-400 font-mono">Daily volume</div>
                    </DataCard>
                </div>

                {/* Missions Table */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-700">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Mission Schedule</h4>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Mission Name</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Aircraft</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Pilot</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Start Time</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {missions.map((mission) => (
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
                                {missions.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            <Target size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
                                            No missions scheduled
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {showCreateModal && (
                    <CreateMissionModal
                        onClose={() => setShowCreateModal(false)}
                        onSuccess={loadData}
                    />
                )}
            </div>
        </DashboardLayout>
    );
}
