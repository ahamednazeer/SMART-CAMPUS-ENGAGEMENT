'use client';

import React from 'react';
import { Target, Clock, CheckCircle, Airplane, MapPin } from '@phosphor-icons/react';
import { Mission } from '@/types';

interface MissionCardProps {
    mission: Mission | null;
    destinationWeather?: any; // Using any for now to avoid circular deps, or import WeatherSnapshot
    onAccept?: (missionId: string) => void;
    loading?: boolean;
}

const missionTypeLabels: Record<string, string> = {
    TRAINING: 'Training',
    PATROL: 'Patrol',
    TRANSPORT: 'Transport',
    MAINTENANCE_FERRY: 'Maintenance Ferry',
    SEARCH_AND_RESCUE: 'SAR',
    OTHER: 'Other',
};

const statusColors: Record<string, string> = {
    PLANNED: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
    IN_PROGRESS: 'bg-green-500/20 text-green-400 border-green-500/40',
    COMPLETED: 'bg-slate-500/20 text-slate-400 border-slate-500/40',
    CANCELLED: 'bg-red-500/20 text-red-400 border-red-500/40',
};

export default function MissionCard({ mission, destinationWeather, onAccept, loading }: MissionCardProps) {
    if (!mission) {
        return (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 h-full">
                <div className="flex items-center gap-2 mb-3">
                    <Target size={20} weight="duotone" className="text-blue-400" />
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Mission</h4>
                </div>
                <div className="flex items-center justify-center h-32 text-slate-500 font-mono text-sm">
                    No missions assigned
                </div>
            </div>
        );
    }

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    return (
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 h-full">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <Target size={20} weight="duotone" className="text-blue-400" />
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Mission</h4>
                </div>
                <span className={`px-2 py-0.5 text-xs font-mono rounded border ${statusColors[mission.status]}`}>
                    {mission.status.replace('_', ' ')}
                </span>
            </div>

            <div className="space-y-3">
                {/* Mission ID and Type */}
                <div>
                    <div className="font-chivo font-bold text-lg text-white truncate">
                        {mission.title}
                    </div>
                    <div className="text-xs text-slate-400 font-mono">
                        {missionTypeLabels[mission.type] || mission.type} • ID: {mission.id.slice(0, 8)}
                    </div>
                </div>

                {/* Times */}
                <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1.5">
                        <Clock size={14} className="text-slate-500" />
                        <span className="font-mono text-slate-300">
                            {formatDate(mission.startTime)} {formatTime(mission.startTime)}
                        </span>
                    </div>
                    {mission.endTime && (
                        <>
                            <span className="text-slate-600">→</span>
                            <span className="font-mono text-slate-300">
                                {formatTime(mission.endTime)}
                            </span>
                        </>
                    )}
                </div>

                {/* Aircraft */}
                {mission.aircraft && (
                    <div className="flex items-center gap-1.5 text-sm">
                        <Airplane size={14} className="text-slate-500" />
                        <span className="font-mono text-slate-300">
                            {mission.aircraft.tailNumber} • {mission.aircraft.type}
                        </span>
                    </div>
                )}
                {/* Destination */}
                {mission.destinationName && (
                    <div className="flex items-center gap-1.5 text-sm">
                        <MapPin size={14} className="text-slate-500" />
                        <span className="font-mono text-slate-300">
                            {mission.destinationName}
                        </span>
                    </div>
                )}

                {/* Destination Weather */}
                {destinationWeather && (
                    <div className="mt-2 p-2 bg-slate-900/40 rounded border border-slate-700/40">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-slate-500 font-mono uppercase">Destination WX</span>
                            <span className="text-xs text-slate-400 font-mono">{destinationWeather.locationName}</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                            <span className="text-white">{destinationWeather.condition}</span>
                            <span className="text-slate-400">{Math.round(destinationWeather.temperature)}°C</span>
                            <span className="text-slate-500 text-xs font-mono">
                                {Math.round(destinationWeather.windSpeed * 1.944)}kt
                            </span>
                        </div>
                    </div>
                )}

                {/* Description */}
                {mission.description && (
                    <div className="text-xs text-slate-400 line-clamp-2">
                        {mission.description}
                    </div>
                )}

                {/* Accept Button */}
                {mission.status === 'PLANNED' && onAccept && (
                    <button
                        onClick={() => onAccept(mission.id)}
                        disabled={loading}
                        className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2 bg-green-600/20 border border-green-500/40 text-green-400 text-sm font-medium rounded-sm hover:bg-green-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <CheckCircle size={16} weight="bold" />
                        {loading ? 'Accepting...' : 'Accept Mission'}
                    </button>
                )}

                {mission.status === 'IN_PROGRESS' && (
                    <div className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2 bg-green-600/20 border border-green-500/40 text-green-400 text-sm font-medium rounded-sm">
                        <CheckCircle size={16} weight="fill" />
                        Mission Accepted
                    </div>
                )}
            </div>
        </div>
    );
}
