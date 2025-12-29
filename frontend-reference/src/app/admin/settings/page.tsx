'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import PlaneSwitch from '@/components/PlaneSwitch';
import { FloppyDisk, ArrowCounterClockwise, Check, Warning } from '@phosphor-icons/react';

interface SystemSettings {
    baseName: string;
    baseLocation?: string;
    timezone: string;
    modules: {
        maintenance: boolean;
        emergency: boolean;
        training: boolean;
        family: boolean;
        fatigue: boolean;
    };
}

export default function SystemSettingsPage() {
    const [settings, setSettings] = useState<SystemSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    const fetchSettings = async () => {
        try {
            const data = await api.getSystemSettings();
            setSettings({
                baseName: data.baseName || '',
                baseLocation: data.baseLocation || '',
                timezone: data.timezone || 'UTC',
                modules: {
                    maintenance: data.modules?.maintenance ?? true,
                    emergency: data.modules?.emergency ?? true,
                    training: data.modules?.training ?? true,
                    family: data.modules?.family ?? true,
                    fatigue: data.modules?.fatigue ?? true,
                }
            });
        } catch (error) {
            console.error('Failed to fetch settings:', error);
            setMessage({ type: 'error', text: 'Failed to load system settings' });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSettings();
    }, []);

    const handleSave = async () => {
        if (!settings) return;
        setSaving(true);
        setMessage(null);

        try {
            await api.updateSystemSettings(settings);
            setMessage({ type: 'success', text: 'Settings saved successfully' });
        } catch (error: any) {
            console.error('Failed to save settings:', error);
            setMessage({ type: 'error', text: error.message || 'Failed to save settings' });
        } finally {
            setSaving(false);
        }
    };

    const handleReset = async () => {
        if (!confirm('Are you sure you want to reset all settings to default values? This cannot be undone.')) return;

        setLoading(true);
        setMessage(null);

        try {
            await api.resetSystemSettings();
            await fetchSettings();
            setMessage({ type: 'success', text: 'Settings reset to defaults' });
        } catch (error: any) {
            console.error('Failed to reset settings:', error);
            setMessage({ type: 'error', text: error.message || 'Failed to reset settings' });
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading settings...</div>
                </div>
            </DashboardLayout>
        );
    }

    if (!settings) {
        return (
            <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
                <div className="text-red-400 font-mono">Failed to load settings.</div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
            <div className="max-w-4xl space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">System Settings</h3>
                    <div className="flex gap-4">
                        <button
                            onClick={handleReset}
                            className="flex items-center gap-2 px-4 py-2.5 border border-slate-700 text-slate-300 hover:bg-slate-800 rounded-sm font-medium tracking-wide uppercase text-sm transition-colors"
                        >
                            <ArrowCounterClockwise size={16} />
                            Reset
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150 disabled:opacity-50"
                        >
                            {saving ? (
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <FloppyDisk size={16} weight="duotone" />
                            )}
                            Save
                        </button>
                    </div>
                </div>

                {message && (
                    <div className={`p-4 rounded-sm flex items-center gap-3 ${message.type === 'success' ? 'bg-green-950/50 text-green-400 border border-green-800' : 'bg-red-950/50 text-red-400 border border-red-800'}`}>
                        {message.type === 'success' ? <Check size={20} weight="bold" /> : <Warning size={20} weight="duotone" />}
                        <span className="font-mono text-sm">{message.text}</span>
                    </div>
                )}

                {/* General Settings */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-6">General Configuration</h4>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-xs text-slate-500 uppercase tracking-wider font-mono">Base Name</label>
                            <input
                                type="text"
                                value={settings.baseName}
                                onChange={(e) => setSettings({ ...settings, baseName: e.target.value })}
                                className="w-full bg-slate-950 border border-slate-700 text-slate-100 rounded-sm text-sm px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
                                placeholder="e.g. AeroOps Airbase"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs text-slate-500 uppercase tracking-wider font-mono">Base Location (City)</label>
                            <input
                                type="text"
                                value={settings.baseLocation || ''}
                                onChange={(e) => setSettings({ ...settings, baseLocation: e.target.value })}
                                className="w-full bg-slate-950 border border-slate-700 text-slate-100 rounded-sm text-sm px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
                                placeholder="e.g. London, Chennai, New York"
                            />
                            <p className="text-[10px] text-slate-500 font-mono">Used for local weather data</p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs text-slate-500 uppercase tracking-wider font-mono">Timezone</label>
                            <select
                                value={settings.timezone}
                                onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                                className="w-full bg-slate-950 border border-slate-700 text-slate-100 rounded-sm text-sm px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
                            >
                                <option value="UTC">UTC</option>
                                <option value="America/New_York">Eastern Time (US & Canada)</option>
                                <option value="America/Chicago">Central Time (US & Canada)</option>
                                <option value="America/Denver">Mountain Time (US & Canada)</option>
                                <option value="America/Los_Angeles">Pacific Time (US & Canada)</option>
                                <option value="Europe/London">London</option>
                                <option value="Asia/Tokyo">Tokyo</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Module Configuration */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                    <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono mb-6">System Modules</h4>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(settings.modules).map(([key, enabled]) => (
                            <div key={key} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-sm border border-slate-800">
                                <div>
                                    <div className="font-medium text-slate-200 capitalize font-mono text-sm">{key} Module</div>
                                    <div className="text-xs text-slate-500 mt-1">Enable or disable {key} functionality</div>
                                </div>
                                <PlaneSwitch
                                    checked={enabled}
                                    onChange={(checked) => setSettings({
                                        ...settings,
                                        modules: { ...settings.modules, [key]: checked }
                                    })}
                                />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
