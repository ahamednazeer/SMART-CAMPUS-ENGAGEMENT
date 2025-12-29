'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { DataCard } from '@/components/DataCard';
import { Airplane, Users, FileText, Siren } from '@phosphor-icons/react';

export default function AdminDashboard() {
    const [stats, setStats] = useState<any>(null);
    const [weather, setWeather] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [userInfo, setUserInfo] = useState({ name: 'Admin', email: 'admin@airbase.mil' });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsData, weatherData] = await Promise.all([
                    api.getSystemStats(),
                    api.getCurrentWeather().catch(() => null),
                ]);
                setStats(statsData);
                setWeather(weatherData);
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <DashboardLayout userRole="ADMIN" userName={userInfo.name} userEmail={userInfo.email}>
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading system statistics...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="ADMIN" userName={userInfo.name} userEmail={userInfo.email}>
            <div className="space-y-6" data-testid="dashboard-overview">
                <div>
                    <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider mb-6">Operational Overview</h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <DataCard
                            title="Total Aircraft"
                            value={stats?.aircraft?.total || 0}
                            icon={Airplane}
                        />
                        <DataCard
                            title="Ready Aircraft"
                            value={stats?.aircraft?.ready || 0}
                            icon={Airplane}
                        />
                        <DataCard
                            title="Total Users"
                            value={stats?.users?.total || 0}
                            icon={Users}
                        />
                        <DataCard
                            title="Emergencies"
                            value={stats?.emergencies?.active || 0}
                            icon={Siren}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Weather Conditions */}
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-4">Weather Conditions</h4>
                        {weather ? (
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Temperature</span>
                                    <span className="text-lg font-mono font-bold">{weather.temperature}°C</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Condition</span>
                                    <span className="text-lg font-mono font-bold">{weather.condition}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Wind Speed</span>
                                    <span className="text-lg font-mono font-bold">{weather.windSpeed} m/s</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Visibility</span>
                                    <span className="text-lg font-mono font-bold">{(weather.visibility / 1000).toFixed(1)} km</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-slate-500 text-sm">Weather data unavailable</p>
                        )}
                    </div>

                    {/* Runway Status */}
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-4">Runway Status</h4>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <span className="text-slate-400 text-sm">Runway 1</span>
                                <span className="text-green-400 text-lg font-mono font-bold">OPEN</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-slate-400 text-sm">Runway 2</span>
                                <span className="text-green-400 text-lg font-mono font-bold">OPEN</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* User Distribution & Aircraft Status */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-4">User Distribution</h4>
                        <div className="space-y-3">
                            {stats?.users?.byRole && Object.entries(stats.users.byRole).map(([role, count]: [string, any]) => (
                                <div key={role} className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm capitalize">{role.toLowerCase().replace('_', ' ')}</span>
                                    <span className="font-mono text-slate-200">{count}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-4">Aircraft Status</h4>
                        <div className="space-y-3">
                            {stats?.aircraft?.byStatus && Object.entries(stats.aircraft.byStatus).map(([status, count]: [string, any]) => (
                                <div key={status} className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm capitalize">{status.replace('_', ' ').toLowerCase()}</span>
                                    <span className="font-mono text-slate-200">{count}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
