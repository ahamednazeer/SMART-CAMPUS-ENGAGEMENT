'use client';

import React from 'react';
import { Airplane, Drop, Wrench, Warning, CheckCircle, Clock } from '@phosphor-icons/react';
import { Aircraft, AircraftStatus, FleetStats } from '@/types';

interface AircraftStatusCardProps {
    aircraft: Aircraft | null;
    fleetStats?: FleetStats;
}

const statusConfig: Record<AircraftStatus, { label: string; color: string; icon: React.ElementType }> = {
    READY: { label: 'READY', color: 'text-green-400 bg-green-500/20 border-green-500/40', icon: CheckCircle },
    IN_MAINTENANCE: { label: 'MAINTENANCE', color: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/40', icon: Wrench },
    GROUNDED: { label: 'GROUNDED', color: 'text-red-400 bg-red-500/20 border-red-500/40', icon: Warning },
    IN_FLIGHT: { label: 'IN FLIGHT', color: 'text-blue-400 bg-blue-500/20 border-blue-500/40', icon: Airplane },
};

export default function AircraftStatusCard({ aircraft, fleetStats }: AircraftStatusCardProps) {
    const renderFuelGauge = (level: number) => {
        const percentage = Math.min(100, Math.max(0, level));
        let color = 'bg-green-500';
        if (percentage < 30) color = 'bg-red-500';
        else if (percentage < 50) color = 'bg-yellow-500';

        return (
            <div className="flex items-center gap-2">
                <Drop size={14} className="text-slate-500" />
                <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${color} transition-all`}
                        style={{ width: `${percentage}%` }}
                    />
                </div>
                <span className={`text-xs font-mono ${percentage < 30 ? 'text-red-400' : percentage < 50 ? 'text-yellow-400' : 'text-green-400'}`}>
                    {percentage.toFixed(0)}%
                </span>
            </div>
        );
    };

    // If no assigned aircraft, show fleet summary
    if (!aircraft && fleetStats) {
        return (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 h-full">
                <div className="flex items-center gap-2 mb-3">
                    <Airplane size={20} weight="duotone" className="text-blue-400" />
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Fleet Status</h4>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <div className="bg-green-500/10 border border-green-500/30 rounded-sm p-2 text-center">
                        <div className="text-2xl font-mono font-bold text-green-400">{fleetStats.READY}</div>
                        <div className="text-xs text-slate-400 uppercase">Ready</div>
                    </div>
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-sm p-2 text-center">
                        <div className="text-2xl font-mono font-bold text-yellow-400">{fleetStats.IN_MAINTENANCE}</div>
                        <div className="text-xs text-slate-400 uppercase">Maintenance</div>
                    </div>
                    <div className="bg-red-500/10 border border-red-500/30 rounded-sm p-2 text-center">
                        <div className="text-2xl font-mono font-bold text-red-400">{fleetStats.GROUNDED}</div>
                        <div className="text-xs text-slate-400 uppercase">Grounded</div>
                    </div>
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-sm p-2 text-center">
                        <div className="text-2xl font-mono font-bold text-blue-400">{fleetStats.IN_FLIGHT}</div>
                        <div className="text-xs text-slate-400 uppercase">In Flight</div>
                    </div>
                </div>
                <div className="mt-3 text-center text-xs text-slate-500 font-mono">
                    Total Fleet: {fleetStats.total} aircraft
                </div>
            </div>
        );
    }

    if (!aircraft) {
        return (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 h-full">
                <div className="flex items-center gap-2 mb-3">
                    <Airplane size={20} weight="duotone" className="text-blue-400" />
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Aircraft</h4>
                </div>
                <div className="flex items-center justify-center h-32 text-slate-500 font-mono text-sm">
                    No aircraft assigned
                </div>
            </div>
        );
    }

    const config = statusConfig[aircraft.status];
    const StatusIcon = config.icon;

    return (
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 h-full">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <Airplane size={20} weight="duotone" className="text-blue-400" />
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Aircraft</h4>
                </div>
                <span className={`flex items-center gap-1 px-2 py-0.5 text-xs font-mono rounded border ${config.color}`}>
                    <StatusIcon size={12} weight="fill" />
                    {config.label}
                </span>
            </div>

            <div className="space-y-3">
                {/* Tail Number and Type */}
                <div>
                    <div className="font-chivo font-bold text-lg text-white">
                        {aircraft.tailNumber}
                    </div>
                    <div className="text-xs text-slate-400 font-mono">
                        {aircraft.type} • {aircraft.model}
                    </div>
                </div>

                {/* Location */}
                {aircraft.location && (
                    <div className="text-sm text-slate-300 font-mono">
                        {aircraft.location}
                    </div>
                )}

                {/* Fuel Level */}
                {aircraft.fuelLevel !== undefined && aircraft.fuelLevel !== null && (
                    <div>
                        <div className="text-xs text-slate-500 mb-1">Fuel Level</div>
                        {renderFuelGauge(aircraft.fuelLevel)}
                    </div>
                )}

                {/* Flight Hours & Next Maintenance */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                    <div>
                        <div className="text-xs text-slate-500">Flight Hours</div>
                        <div className="font-mono text-sm text-slate-300">{aircraft.flightHours?.toFixed(1) || 0} hrs</div>
                    </div>
                    {aircraft.nextMaintenance && (
                        <div>
                            <div className="text-xs text-slate-500 flex items-center gap-1">
                                <Clock size={10} />
                                Next Maint.
                            </div>
                            <div className="font-mono text-sm text-yellow-400">
                                {new Date(aircraft.nextMaintenance).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
