'use client';

import React, { useState } from 'react';
import {
    Cloud, Wind, Eye, Thermometer, Drop, ArrowUp,
    Warning, Phone, CaretDown, CaretUp, Clock, ArrowsClockwise
} from '@phosphor-icons/react';
import { WeatherSnapshot, RunwayStatus } from '@/types';

interface WeatherCardProps {
    weather: WeatherSnapshot | null;
    runwayStatus?: RunwayStatus;
    destinationWeather?: WeatherSnapshot | null;
    onRequestOpsAdvice?: () => void;
    onRefresh?: () => void;
}

const runwayStatusConfig: Record<RunwayStatus, { label: string; color: string; bgColor: string }> = {
    OPEN: {
        label: 'RWY OPEN',
        color: 'text-green-400',
        bgColor: 'bg-green-500/20 border-green-500/40'
    },
    CAUTION: {
        label: 'RWY CAUTION',
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/20 border-yellow-500/40'
    },
    CLOSED: {
        label: 'RWY CLOSED',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20 border-red-500/40'
    },
    UNKNOWN: {
        label: 'RWY UNKNOWN',
        color: 'text-slate-400',
        bgColor: 'bg-slate-500/20 border-slate-500/40'
    },
};

const conditionIcons: Record<string, string> = {
    Clear: '☀️',
    Clouds: '☁️',
    Rain: '🌧️',
    Drizzle: '🌦️',
    Thunderstorm: '⛈️',
    Snow: '❄️',
    Mist: '🌫️',
    Fog: '🌫️',
    Haze: '🌫️',
};

export default function WeatherCard({
    weather,
    runwayStatus = 'UNKNOWN',
    destinationWeather,
    onRequestOpsAdvice,
    onRefresh
}: WeatherCardProps) {
    const [expanded, setExpanded] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    const handleRefresh = async () => {
        if (onRefresh) {
            setRefreshing(true);
            await onRefresh();
            setTimeout(() => setRefreshing(false), 1000);
        }
    };

    if (!weather) {
        return (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 h-full">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Cloud size={20} weight="duotone" className="text-blue-400" />
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Weather</h4>
                    </div>
                    {onRefresh && (
                        <button
                            onClick={handleRefresh}
                            className={`text-slate-500 hover:text-blue-400 transition-colors ${refreshing ? 'animate-spin' : ''}`}
                            title="Refresh Weather"
                        >
                            <ArrowsClockwise size={16} />
                        </button>
                    )}
                </div>
                <div className="flex items-center justify-center h-32 text-slate-500 font-mono text-sm">
                    Weather data unavailable
                </div>
            </div>
        );
    }

    const windKts = Math.round(weather.windSpeed * 1.944);
    const gustKts = weather.windGust ? Math.round(weather.windGust * 1.944) : null;
    const visMiles = weather.visibility
        ? Math.round(weather.visibility / 1609.34 * 10) / 10
        : null;
    const rwyConfig = runwayStatusConfig[weather.runwayStatus || runwayStatus];
    const windRotation = weather.windDirection || 0;

    // Check if weather is stale
    const isStale = weather.isStale;
    const staleMinutes = weather.staleSince
        ? Math.floor((Date.now() - new Date(weather.staleSince).getTime()) / 60000)
        : 0;

    const formatTimestamp = (ts: string) => {
        const date = new Date(ts);
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    };

    return (
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 h-full">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <Cloud size={20} weight="duotone" className="text-blue-400" />
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">
                        Weather {weather.locationName ? `• ${weather.locationName}` : ''}
                    </h4>
                    {isStale && (
                        <span className="flex items-center gap-1 text-xs text-yellow-400 font-mono">
                            <Warning size={12} /> STALE ({staleMinutes}m)
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {onRefresh && (
                        <button
                            onClick={handleRefresh}
                            className={`text-slate-500 hover:text-blue-400 transition-colors ${refreshing ? 'animate-spin' : ''}`}
                            title="Refresh Weather"
                        >
                            <ArrowsClockwise size={16} />
                        </button>
                    )}
                    <span className={`px-2 py-0.5 text-xs font-mono rounded border ${rwyConfig.bgColor} ${rwyConfig.color}`}>
                        {rwyConfig.label}
                        {weather.isOverride && ' (MANUAL)'}
                    </span>
                </div>
            </div>

            {/* Severe Weather Alert */}
            {weather.severeWeather && weather.severeWeather.length > 0 && (
                <div className="mb-3 flex items-center gap-2 px-2 py-1.5 bg-red-500/20 border border-red-500/40 rounded-sm">
                    <Warning size={14} className="text-red-400" weight="fill" />
                    <span className="text-xs font-mono text-red-300 uppercase">
                        {weather.severeWeather.join(' • ')}
                    </span>
                </div>
            )}

            <div className="space-y-3">
                {/* Condition and Temperature */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-3xl">{conditionIcons[weather.condition] || '🌤️'}</span>
                        <div>
                            <div className="font-chivo font-bold text-lg text-white">{weather.condition}</div>
                            <div className="text-xs text-slate-400 font-mono">
                                {weather.precipitation && weather.precipitation !== 'None' && (
                                    <span className="text-blue-400">{weather.precipitation}</span>
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="font-mono text-2xl font-bold text-white">
                            {Math.round(weather.temperature)}°C
                        </div>
                        <div className="text-xs text-slate-400 font-mono">
                            {Math.round(weather.temperature * 9 / 5 + 32)}°F
                        </div>
                    </div>
                </div>

                {/* METAR-style formatted weather */}
                {weather.formattedWeather && (
                    <div className="bg-slate-900/50 border border-slate-700/40 rounded-sm px-3 py-2">
                        <div className="text-xs text-green-400 font-mono tracking-wide">
                            {weather.formattedWeather}
                        </div>
                    </div>
                )}

                {/* Weather details grid */}
                <div className="grid grid-cols-3 gap-2">
                    {/* Wind */}
                    <div className="bg-slate-900/30 rounded-sm p-2 text-center">
                        <div className="flex items-center justify-center gap-1 text-slate-400 mb-1">
                            <Wind size={14} />
                            <ArrowUp
                                size={12}
                                style={{ transform: `rotate(${windRotation + 180}deg)` }}
                                className="text-blue-400"
                            />
                        </div>
                        <div className="font-mono text-sm text-white">
                            {windKts}{gustKts && gustKts > windKts ? `G${gustKts}` : ''} KT
                        </div>
                        <div className="text-xs text-slate-500">Wind</div>
                    </div>

                    {/* Visibility */}
                    <div className="bg-slate-900/30 rounded-sm p-2 text-center">
                        <Eye size={14} className="mx-auto text-slate-400 mb-1" />
                        <div className="font-mono text-sm text-white">
                            {visMiles !== null ? `${visMiles} SM` : 'N/A'}
                        </div>
                        <div className="text-xs text-slate-500">Visibility</div>
                    </div>

                    {/* Ceiling */}
                    <div className="bg-slate-900/30 rounded-sm p-2 text-center">
                        <Cloud size={14} className="mx-auto text-slate-400 mb-1" />
                        <div className="font-mono text-sm text-white">
                            {weather.ceiling ? `${weather.ceiling} FT` : 'CLR'}
                        </div>
                        <div className="text-xs text-slate-500">Ceiling</div>
                    </div>
                </div>

                {/* Expandable details */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="w-full flex items-center justify-center gap-1 text-xs text-slate-400 hover:text-slate-300 transition-colors py-1"
                >
                    {expanded ? <CaretUp size={12} /> : <CaretDown size={12} />}
                    {expanded ? 'Less details' : 'More details'}
                </button>

                {expanded && (
                    <div className="space-y-2 pt-1 border-t border-slate-700/40">
                        {/* Status Reason */}
                        {weather.runwayStatusReason && (
                            <div className="text-xs text-slate-400">
                                <span className="text-slate-500">Status Reason: </span>
                                {weather.runwayStatusReason}
                            </div>
                        )}

                        {/* Status Factors */}
                        {weather.runwayStatusFactors && weather.runwayStatusFactors.length > 0 && (
                            <div className="text-xs">
                                <span className="text-slate-500">Factors: </span>
                                <ul className="list-disc list-inside text-slate-400">
                                    {weather.runwayStatusFactors.map((factor, i) => (
                                        <li key={i}>{factor}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Additional metrics grid */}
                        <div className="grid grid-cols-3 gap-2">
                            <div className="text-center">
                                <div className="text-xs text-slate-500">Humidity</div>
                                <div className="font-mono text-sm text-slate-300">
                                    {weather.humidity || 'N/A'}%
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-xs text-slate-500">Pressure</div>
                                <div className="font-mono text-sm text-slate-300">
                                    {weather.pressure || 'N/A'} hPa
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-xs text-slate-500">Updated</div>
                                <div className="font-mono text-sm text-slate-300">
                                    {formatTimestamp(weather.timestamp)}
                                </div>
                            </div>
                        </div>

                        {/* Override info */}
                        {weather.isOverride && (
                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-sm px-2 py-1.5 text-xs">
                                <span className="text-yellow-400 font-medium">Manual Override</span>
                                <span className="text-slate-400"> by {weather.overrideBy}</span>
                                {weather.overrideExpiry && (
                                    <span className="text-slate-500">
                                        {' '}• Expires: {new Date(weather.overrideExpiry).toLocaleTimeString()}
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Request Ops Advice Button */}
                {onRequestOpsAdvice && (
                    <button
                        onClick={onRequestOpsAdvice}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-blue-600/20 border border-blue-500/40 text-blue-400 text-sm font-medium rounded-sm hover:bg-blue-600/30 transition-all"
                    >
                        <Phone size={14} />
                        Request Ops Advice
                    </button>
                )}

                {/* Timestamp */}
                <div className="flex items-center justify-center gap-1 text-xs text-slate-500 font-mono">
                    <Clock size={10} />
                    Last update: {formatTimestamp(weather.timestamp)}
                </div>
            </div>

            {/* Destination Weather (if provided) */}
            {destinationWeather && (
                <div className="mt-4 pt-3 border-t border-slate-700/40">
                    <div className="text-xs text-slate-500 uppercase tracking-wider mb-2 font-mono">
                        Destination Weather
                    </div>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className="text-xl">{conditionIcons[destinationWeather.condition] || '🌤️'}</span>
                            <div>
                                <div className="text-sm font-medium text-white">{destinationWeather.condition}</div>
                                <div className="text-xs text-slate-400 font-mono">
                                    {Math.round(destinationWeather.windSpeed * 1.944)} KT
                                </div>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="font-mono text-lg text-white">
                                {Math.round(destinationWeather.temperature)}°C
                            </div>
                            <span className={`px-1.5 py-0.5 text-xs font-mono rounded border ${runwayStatusConfig[destinationWeather.runwayStatus || 'UNKNOWN'].bgColor
                                } ${runwayStatusConfig[destinationWeather.runwayStatus || 'UNKNOWN'].color}`}>
                                {runwayStatusConfig[destinationWeather.runwayStatus || 'UNKNOWN'].label}
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
