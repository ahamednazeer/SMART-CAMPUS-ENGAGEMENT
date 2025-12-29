'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { StatusBadge } from '@/components/StatusBadge';
import { Target, MagnifyingGlass } from '@phosphor-icons/react';

import WeatherDetailsModal from '@/components/pilot/WeatherDetailsModal';

export default function PilotMissionsPage() {
    const [missions, setMissions] = useState<any[]>([]);
    const [weatherData, setWeatherData] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedWeather, setSelectedWeather] = useState<any>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await api.getMissions();
            setMissions(data);

            // Fetch weather for missions with destination coordinates
            const weatherMap: Record<string, any> = {};
            const weatherPromises = data
                .filter((m: any) => m.destinationLat && m.destinationLon && (m.status === 'PLANNED' || m.status === 'IN_PROGRESS'))
                .map(async (m: any) => {
                    try {
                        const weather = await api.getWeatherByLocation(m.destinationLat, m.destinationLon);
                        weatherMap[m.id] = weather;
                    } catch (e) {
                        console.error(`Failed to fetch weather for mission ${m.id}`, e);
                    }
                });

            await Promise.allSettled(weatherPromises);
            setWeatherData(weatherMap);
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
            <DashboardLayout userRole="PILOT" userName="Pilot" userEmail="pilot@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading missions...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="PILOT" userName="Pilot" userEmail="pilot@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">My Missions</h3>

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
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Destination</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Dest. Weather</th>
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
                                        <td className="px-6 py-4 font-mono text-sm">{mission.destinationName || '-'}</td>
                                        <td className="px-6 py-4 font-mono text-sm">
                                            {mission.destinationLat && mission.destinationLon ? (
                                                weatherData[mission.id] ? (
                                                    <div
                                                        className="flex flex-col cursor-pointer hover:bg-slate-700/50 p-1.5 -m-1.5 rounded transition-colors group"
                                                        onClick={() => setSelectedWeather({ ...weatherData[mission.id], locationName: mission.destinationName })}
                                                    >
                                                        <span className="text-white group-hover:text-blue-400 transition-colors">{weatherData[mission.id].condition}</span>
                                                        <span className="text-xs text-slate-400">
                                                            {Math.round(weatherData[mission.id].temperature)}°C • {Math.round(weatherData[mission.id].windSpeed * 1.944)}kt
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <span className="text-slate-500 text-xs italic">Loading...</span>
                                                )
                                            ) : (
                                                <span className="text-slate-600 text-xs">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-sm">{new Date(mission.startTime).toLocaleString()}</td>
                                        <td className="px-6 py-4"><StatusBadge status={mission.status} /></td>
                                    </tr>
                                ))}
                                {filteredMissions.length === 0 && (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            <Target size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
                                            No missions assigned
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {selectedWeather && (
                <WeatherDetailsModal
                    weather={selectedWeather}
                    onClose={() => setSelectedWeather(null)}
                    onRefresh={async () => {
                        if (selectedWeather && selectedWeather.locationName) {
                            // Find mission with this location name to get lat/lon
                            // Note: We stored locationName in selectedWeather when opening modal
                            const mission = missions.find(m => m.destinationName === selectedWeather.locationName);
                            if (mission && mission.destinationLat && mission.destinationLon) {
                                try {
                                    const newWeather = await api.getWeatherByLocation(mission.destinationLat, mission.destinationLon);
                                    // Update global weather state
                                    setWeatherData(prev => ({
                                        ...prev,
                                        [mission.id]: newWeather
                                    }));
                                    // Update modal state
                                    setSelectedWeather({ ...newWeather, locationName: mission.destinationName });
                                } catch (e) {
                                    console.error('Failed to refresh weather', e);
                                }
                            }
                        }
                    }}
                />
            )}
        </DashboardLayout>
    );
}
