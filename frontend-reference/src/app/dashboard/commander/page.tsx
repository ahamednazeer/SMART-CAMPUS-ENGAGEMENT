'use client';

import React, { useEffect, useState } from 'react';
import { Shield, Users, Cloud, Siren } from '@phosphor-icons/react';
import DashboardLayout from '@/components/DashboardLayout';
import { DataCard } from '@/components/DataCard';
import { api } from '@/lib/api';

export default function CommanderDashboard() {
    const [stats, setStats] = useState<any>(null);
    const [weather, setWeather] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [statsData, weatherData] = await Promise.all([
                api.getSystemStats(),
                api.getCurrentWeather().catch(() => null),
            ]);
            setStats(statsData);
            setWeather(weatherData);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="COMMANDER" userName="Commander" userEmail="commander@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="COMMANDER" userName="Commander" userEmail="commander@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Base Overview</h3>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <DataCard
                        title="Base Readiness"
                        value="92%"
                        icon={Shield}
                    >
                        <div className="text-xs text-green-400 font-mono">Operational</div>
                    </DataCard>

                    <DataCard
                        title="Active Personnel"
                        value={stats?.users?.total || 0}
                        icon={Users}
                    >
                        <div className="text-xs text-blue-400 font-mono">On duty</div>
                    </DataCard>

                    <DataCard
                        title="Weather Condition"
                        value={weather?.condition || 'Unknown'}
                        icon={Cloud}
                    >
                        <div className="text-xs text-slate-400 font-mono">
                            {weather?.temperature ? `${weather.temperature}°C` : 'N/A'}
                        </div>
                    </DataCard>

                    <DataCard
                        title="Emergencies"
                        value={stats?.emergencies?.active || 0}
                        icon={Siren}
                    >
                        <div className="text-xs text-green-400 font-mono">No active threats</div>
                    </DataCard>
                </div>

                {/* Weather Details */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-4">Weather Conditions</h4>
                        {weather ? (
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Temperature</span>
                                    <span className="text-lg font-mono font-bold">{weather.temperature}°C</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Wind Speed</span>
                                    <span className="text-lg font-mono font-bold">{weather.windSpeed} m/s</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Visibility</span>
                                    <span className="text-lg font-mono font-bold">{(weather.visibility / 1000).toFixed(1)} km</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Humidity</span>
                                    <span className="text-lg font-mono font-bold">{weather.humidity}%</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400 text-sm">Pressure</span>
                                    <span className="text-lg font-mono font-bold">{weather.pressure} hPa</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-slate-500 text-sm">Weather data unavailable</p>
                        )}
                    </div>

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
            </div>
        </DashboardLayout>
    );
}
