'use client';

import React, { useEffect, useState } from 'react';
import { Siren, Clock, CheckCircle, Fire, Warning, Crosshair } from '@phosphor-icons/react';
import DashboardLayout from '@/components/DashboardLayout';
import { DataCard } from '@/components/DataCard';
import { StatusBadge } from '@/components/StatusBadge';
import { api } from '@/lib/api';

interface Emergency {
    id: string;
    type: string;
    title: string;
    description: string;
    location: string;
    status: string;
    severity: string;
    createdAt: string;
    timeline?: { event: string; createdAt: string }[];
}

interface DashboardData {
    activeEmergencies: Emergency[];
    resolvingEmergencies: Emergency[];
    recentCompleted: Emergency[];
    incidentWeather: {
        windSpeed?: number;
        visibility?: number;
        temperature?: number;
        precipitation?: string;
        condition?: string;
    } | null;
    myAssignments: { emergency: Emergency }[];
    stats: {
        active: number;
        resolving: number;
        myAssigned: number;
    };
}

export default function EmergencyDashboard() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const dashboardData = await api.getEmergencyDashboard();
            setData(dashboardData);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusUpdate = async (id: string, status: string) => {
        try {
            await api.updateEmergencyStatus(id, status);
            loadData();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="EMERGENCY" userName="Emergency Team" userEmail="emergency@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="EMERGENCY" userName="Emergency Team" userEmail="emergency@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Emergency Response Center</h3>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <DataCard
                        title="Active Emergencies"
                        value={data?.stats.active || 0}
                        icon={Siren}
                    >
                        <div className="text-xs text-red-400 font-mono">Requires response</div>
                    </DataCard>

                    <DataCard
                        title="Resolving"
                        value={data?.stats.resolving || 0}
                        icon={Crosshair}
                    >
                        <div className="text-xs text-yellow-400 font-mono">In progress</div>
                    </DataCard>

                    <DataCard
                        title="My Assignments"
                        value={data?.stats.myAssigned || 0}
                        icon={Clock}
                    >
                        <div className="text-xs text-blue-400 font-mono">Assigned to you</div>
                    </DataCard>

                    <DataCard
                        title="Weather"
                        value={data?.incidentWeather?.condition || 'N/A'}
                        icon={Warning}
                    >
                        <div className="text-xs text-slate-400 font-mono">
                            {data?.incidentWeather?.windSpeed ? `Wind: ${data.incidentWeather.windSpeed} m/s` : 'No data'}
                        </div>
                    </DataCard>
                </div>

                {/* Active Emergencies */}
                <div className="bg-slate-800/40 border border-red-900/50 rounded-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-2">
                        <Fire className="text-red-500" size={20} weight="fill" />
                        <h4 className="text-red-400 text-xs uppercase tracking-wider font-mono">Active Emergencies</h4>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Title</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Location</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Severity</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {data?.activeEmergencies.map((emergency) => (
                                    <tr key={emergency.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{emergency.type}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{emergency.title}</td>
                                        <td className="px-6 py-4 text-sm text-slate-400">{emergency.location}</td>
                                        <td className="px-6 py-4"><StatusBadge status={emergency.severity} /></td>
                                        <td className="px-6 py-4"><StatusBadge status={emergency.status} /></td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => handleStatusUpdate(emergency.id, 'RESOLVING')}
                                                className="px-3 py-1.5 text-xs bg-yellow-950/50 text-yellow-400 border border-yellow-800 rounded-sm hover:bg-yellow-900/50 font-mono uppercase tracking-wider"
                                            >
                                                Start Response
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {(!data?.activeEmergencies || data.activeEmergencies.length === 0) && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            <CheckCircle size={32} className="mx-auto mb-2 text-green-500" />
                                            No active emergencies
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Resolving Emergencies */}
                {data?.resolvingEmergencies && data.resolvingEmergencies.length > 0 && (
                    <div className="bg-slate-800/40 border border-yellow-900/50 rounded-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-700">
                            <h4 className="text-yellow-400 text-xs uppercase tracking-wider font-mono">Emergencies In Progress</h4>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-slate-900/50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Type</th>
                                        <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Title</th>
                                        <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Location</th>
                                        <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/50">
                                    {data.resolvingEmergencies.map((emergency) => (
                                        <tr key={emergency.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-6 py-4 font-mono text-sm">{emergency.type}</td>
                                            <td className="px-6 py-4 text-sm text-slate-300">{emergency.title}</td>
                                            <td className="px-6 py-4 text-sm text-slate-400">{emergency.location}</td>
                                            <td className="px-6 py-4">
                                                <button
                                                    onClick={() => handleStatusUpdate(emergency.id, 'COMPLETED')}
                                                    className="px-3 py-1.5 text-xs bg-green-950/50 text-green-400 border border-green-800 rounded-sm hover:bg-green-900/50 font-mono uppercase tracking-wider"
                                                >
                                                    Mark Resolved
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Incident Weather */}
                {data?.incidentWeather && (
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-4">Incident Weather Conditions</h4>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-slate-100">{data.incidentWeather.temperature?.toFixed(1) || '--'}°C</div>
                                <div className="text-xs text-slate-500 font-mono">Temperature</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-slate-100">{data.incidentWeather.windSpeed || '--'} m/s</div>
                                <div className="text-xs text-slate-500 font-mono">Wind Speed</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-slate-100">{data.incidentWeather.visibility || '--'} m</div>
                                <div className="text-xs text-slate-500 font-mono">Visibility</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-slate-100">{data.incidentWeather.precipitation || 'None'}</div>
                                <div className="text-xs text-slate-500 font-mono">Precipitation</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-slate-100">{data.incidentWeather.condition || '--'}</div>
                                <div className="text-xs text-slate-500 font-mono">Conditions</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
