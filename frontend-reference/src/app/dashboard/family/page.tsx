'use client';

import React, { useEffect, useState } from 'react';
import { House, Heart, Megaphone, Phone, Info, Buildings } from '@phosphor-icons/react';
import DashboardLayout from '@/components/DashboardLayout';
import { DataCard } from '@/components/DataCard';
import { api } from '@/lib/api';

interface ContentItem {
    id: string;
    category: string;
    title: string;
    content: string;
    createdAt: string;
}

interface DashboardData {
    welfare: ContentItem[];
    services: ContentItem[];
    announcements: ContentItem[];
    stats: {
        welfareCount: number;
        servicesCount: number;
        announcementsCount: number;
    };
}

export default function FamilyDashboard() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'welfare' | 'services' | 'announcements'>('announcements');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const dashboardData = await api.getFamilyDashboard();
            setData(dashboardData);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="FAMILY" userName="Family Member" userEmail="family@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading...</div>
                </div>
            </DashboardLayout>
        );
    }

    const getActiveContent = () => {
        switch (activeTab) {
            case 'welfare':
                return data?.welfare || [];
            case 'services':
                return data?.services || [];
            case 'announcements':
                return data?.announcements || [];
            default:
                return [];
        }
    };

    const getTabIcon = (tab: string) => {
        switch (tab) {
            case 'welfare':
                return House;
            case 'services':
                return Heart;
            case 'announcements':
                return Megaphone;
            default:
                return Info;
        }
    };

    return (
        <DashboardLayout userRole="FAMILY" userName="Family Member" userEmail="family@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Family Support Portal</h3>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <DataCard
                        title="Welfare Resources"
                        value={data?.stats.welfareCount || 0}
                        icon={House}
                    >
                        <div className="text-xs text-blue-400 font-mono">Housing, Schools, etc.</div>
                    </DataCard>

                    <DataCard
                        title="Services"
                        value={data?.stats.servicesCount || 0}
                        icon={Heart}
                    >
                        <div className="text-xs text-green-400 font-mono">Medical, Support</div>
                    </DataCard>

                    <DataCard
                        title="Announcements"
                        value={data?.stats.announcementsCount || 0}
                        icon={Megaphone}
                    >
                        <div className="text-xs text-yellow-400 font-mono">Latest updates</div>
                    </DataCard>
                </div>

                {/* Tab Navigation */}
                <div className="flex gap-2 border-b border-slate-700">
                    {(['announcements', 'welfare', 'services'] as const).map((tab) => {
                        const Icon = getTabIcon(tab);
                        return (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`flex items-center gap-2 px-4 py-3 text-sm font-mono uppercase tracking-wider transition-colors ${activeTab === tab
                                        ? 'text-blue-400 border-b-2 border-blue-400 -mb-[1px]'
                                        : 'text-slate-500 hover:text-slate-300'
                                    }`}
                            >
                                <Icon size={16} />
                                {tab}
                            </button>
                        );
                    })}
                </div>

                {/* Content Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {getActiveContent().map((item) => (
                        <div
                            key={item.id}
                            className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6 hover:border-slate-600 transition-colors"
                        >
                            <div className="flex items-start gap-3">
                                <div className={`w-10 h-10 rounded-sm flex items-center justify-center ${activeTab === 'welfare'
                                        ? 'bg-blue-950/50 text-blue-400'
                                        : activeTab === 'services'
                                            ? 'bg-green-950/50 text-green-400'
                                            : 'bg-yellow-950/50 text-yellow-400'
                                    }`}>
                                    {activeTab === 'welfare' && <Buildings size={20} />}
                                    {activeTab === 'services' && <Heart size={20} />}
                                    {activeTab === 'announcements' && <Megaphone size={20} />}
                                </div>
                                <div className="flex-1">
                                    <h4 className="font-semibold text-slate-100 mb-2">{item.title}</h4>
                                    <p className="text-sm text-slate-400 leading-relaxed">{item.content}</p>
                                    <div className="mt-3 text-xs text-slate-500 font-mono">
                                        {new Date(item.createdAt).toLocaleDateString()}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                    {getActiveContent().length === 0 && (
                        <div className="col-span-full text-center py-12 text-slate-500 font-mono">
                            No {activeTab} content available
                        </div>
                    )}
                </div>

                {/* Contact Information */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Phone className="text-blue-400" size={20} />
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Support Contacts</h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-900/50 border border-slate-700 rounded-sm p-4">
                            <div className="text-sm font-semibold text-slate-100 mb-1">Family Support Office</div>
                            <div className="text-xs text-slate-400">Mon-Fri: 8AM - 5PM</div>
                            <div className="text-sm text-blue-400 font-mono mt-2">+1 (555) 123-4567</div>
                        </div>
                        <div className="bg-slate-900/50 border border-slate-700 rounded-sm p-4">
                            <div className="text-sm font-semibold text-slate-100 mb-1">Medical Center</div>
                            <div className="text-xs text-slate-400">24/7 Emergency Services</div>
                            <div className="text-sm text-blue-400 font-mono mt-2">+1 (555) 987-6543</div>
                        </div>
                        <div className="bg-slate-900/50 border border-slate-700 rounded-sm p-4">
                            <div className="text-sm font-semibold text-slate-100 mb-1">Housing Office</div>
                            <div className="text-xs text-slate-400">Mon-Fri: 9AM - 4PM</div>
                            <div className="text-sm text-blue-400 font-mono mt-2">+1 (555) 456-7890</div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
