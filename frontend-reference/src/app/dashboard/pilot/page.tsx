'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { ArrowsClockwise } from '@phosphor-icons/react';
import DashboardLayout from '@/components/DashboardLayout';
import MissionCard from '@/components/pilot/MissionCard';
import AircraftStatusCard from '@/components/pilot/AircraftStatusCard';
import WeatherCard from '@/components/pilot/WeatherCard';
import AlertsBanner from '@/components/pilot/AlertsBanner';
import MaintenanceSummary from '@/components/pilot/MaintenanceSummary';
import QuickActions from '@/components/pilot/QuickActions';
import ChatBot from '@/components/ChatBot';
import { api } from '@/lib/api';
import { PilotDashboardData } from '@/types';

export default function PilotDashboard() {
    const [dashboardData, setDashboardData] = useState<PilotDashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [acceptingMission, setAcceptingMission] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [chatOpen, setChatOpen] = useState(false);
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

    const loadDashboardData = useCallback(async (showLoading = true, forceRefresh = false) => {
        try {
            if (showLoading) setLoading(true);
            setError(null);
            const data = await api.getPilotDashboard(forceRefresh);
            setDashboardData(data);
            setLastRefresh(new Date());
        } catch (err: any) {
            console.error('Failed to load dashboard:', err);
            setError(err.message || 'Failed to load dashboard data');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        loadDashboardData();

        // Auto-refresh every 5 minutes
        const interval = setInterval(() => {
            loadDashboardData(false);
        }, 5 * 60 * 1000);

        return () => clearInterval(interval);
    }, [loadDashboardData]);

    const handleRefresh = async () => {
        setRefreshing(true);
        await loadDashboardData(false, true);
    };

    const handleAcceptMission = async (missionId: string) => {
        try {
            setAcceptingMission(true);
            await api.acknowledgeMission(missionId);
            await loadDashboardData(false);
        } catch (err: any) {
            console.error('Failed to accept mission:', err);
            alert(err.message || 'Failed to accept mission');
        } finally {
            setAcceptingMission(false);
        }
    };

    const handleDismissAlert = async (alertId: string) => {
        try {
            await api.markAlertRead(alertId);
            await loadDashboardData(false);
        } catch (err) {
            console.error('Failed to dismiss alert:', err);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="PILOT" userName="Pilot" userEmail="pilot@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                        <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full mx-auto mb-4" />
                        <div className="text-slate-400 font-mono">Loading dashboard...</div>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    if (error) {
        return (
            <DashboardLayout userRole="PILOT" userName="Pilot" userEmail="pilot@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                        <div className="text-red-400 font-mono mb-4">⚠️ {error}</div>
                        <button
                            onClick={() => loadDashboardData()}
                            className="px-4 py-2 bg-blue-600/20 border border-blue-500/40 text-blue-400 rounded-sm hover:bg-blue-600/30 transition-all font-mono text-sm"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout
            userRole="PILOT"
            userName={dashboardData?.pilot?.name || "Pilot"}
            userEmail={dashboardData?.pilot?.email || "pilot@airbase.mil"}
        >
            <div className="space-y-6">
                {/* Header with refresh */}
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Pilot Dashboard</h3>
                        <p className="text-xs text-slate-500 font-mono mt-1">
                            Last updated: {lastRefresh.toLocaleTimeString()}
                        </p>
                    </div>
                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="flex items-center gap-2 px-3 py-2 bg-slate-800/60 border border-slate-700 text-slate-300 rounded-sm hover:bg-slate-700/60 transition-all disabled:opacity-50"
                    >
                        <ArrowsClockwise
                            size={16}
                            className={refreshing ? 'animate-spin' : ''}
                        />
                        <span className="text-sm font-mono">Refresh</span>
                    </button>
                </div>

                {/* Alerts Banner (if any alerts exist) */}
                {dashboardData && (dashboardData.alerts.length > 0 || dashboardData.activeEmergencies.length > 0) && (
                    <AlertsBanner
                        alerts={dashboardData.alerts}
                        emergencies={dashboardData.activeEmergencies}
                        onDismiss={handleDismissAlert}
                    />
                )}

                {/* Main Cards Grid - Top Row */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Mission Card */}
                    {/* Mission Card */}
                    <MissionCard
                        mission={dashboardData?.nextMission || null}
                        destinationWeather={dashboardData?.destinationWeather}
                        onAccept={handleAcceptMission}
                        loading={acceptingMission}
                    />

                    {/* Aircraft Status Card */}
                    <AircraftStatusCard
                        aircraft={dashboardData?.assignedAircraft || null}
                        fleetStats={dashboardData?.fleetStats}
                    />

                    {/* Weather Card */}
                    <WeatherCard
                        weather={dashboardData?.weather || null}
                        runwayStatus={dashboardData?.runwayStatus as any}
                        destinationWeather={dashboardData?.destinationWeather}
                        onRequestOpsAdvice={() => {
                            alert('Contact Ops for weather advice:\n📞 Ops Desk: 123-456-7891\n📧 ops@airbase.mil');
                        }}
                        onRefresh={() => loadDashboardData(false, true)}
                    />
                </div>

                {/* Quick Actions */}
                <QuickActions
                    onOpenChecklist={() => {
                        // Navigate to documents or open modal
                        window.location.href = '/dashboard/pilot/aircraft';
                    }}
                    onContactOps={() => {
                        // Could open a modal with contact info
                        alert('Contact Ops:\n📞 ATC: 123-456-7890\n📞 Ops Desk: 123-456-7891');
                    }}
                    onReportIssue={() => {
                        // Could open a report issue modal
                        alert('Report Issue functionality - Coming Soon');
                    }}
                    onViewDocuments={() => {
                        window.location.href = '/dashboard/pilot/missions';
                    }}
                    onOpenAI={() => setChatOpen(true)}
                />

                {/* Bottom Section - Maintenance and other info */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Maintenance Summary */}
                    <MaintenanceSummary logs={dashboardData?.recentMaintenance || []} />

                    {/* Additional Missions (if any) */}
                    {dashboardData && dashboardData.missions.length > 1 && (
                        <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4">
                            <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-3">
                                Upcoming Missions ({dashboardData.missions.length})
                            </h4>
                            <div className="space-y-2">
                                {dashboardData.missions.slice(1, 4).map((mission) => (
                                    <div
                                        key={mission.id}
                                        className="flex items-center justify-between p-2 bg-slate-900/40 border border-slate-700/40 rounded-sm"
                                    >
                                        <div>
                                            <div className="text-sm font-medium text-white truncate">
                                                {mission.title}
                                            </div>
                                            <div className="text-xs text-slate-400 font-mono">
                                                {new Date(mission.startTime).toLocaleDateString('en-US', {
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </div>
                                        </div>
                                        <span className={`px-2 py-0.5 text-xs font-mono rounded border ${mission.status === 'PLANNED'
                                            ? 'bg-blue-500/20 text-blue-400 border-blue-500/40'
                                            : 'bg-green-500/20 text-green-400 border-green-500/40'
                                            }`}>
                                            {mission.status.replace('_', ' ')}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Placeholder for NOTAM highlights when no extra missions */}
                    {(!dashboardData || dashboardData.missions.length <= 1) && (
                        <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4">
                            <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-3">
                                NOTAM Highlights
                            </h4>
                            <div className="text-center text-slate-500 font-mono text-sm py-6">
                                No active NOTAMs
                            </div>
                            <div className="text-xs text-slate-600 text-center font-mono">
                                Check with Ops for the latest notices
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* AI Chatbot */}
            <ChatBot isOpen={chatOpen} onClose={() => setChatOpen(false)} />
        </DashboardLayout>
    );
}
