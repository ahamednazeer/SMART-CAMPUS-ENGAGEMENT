'use client';

import React, { useState, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
    Airplane,
    SignOut,
    Wrench,
    Target,
    Siren,
    GraduationCap,
    House,
    Robot,
    Gauge,
    Users,
    Gear,
    FileText,
    ChartLineUp,
    GlobeHemisphereWest,
} from '@phosphor-icons/react';
import ChatBot from './ChatBot';

interface MenuItem {
    icon: React.ElementType;
    label: string;
    path: string;
}

interface DashboardLayoutProps {
    children: ReactNode;
    userRole?: string;
    userName?: string;
    userEmail?: string;
}

const menuItemsByRole: Record<string, MenuItem[]> = {
    ADMIN: [
        { icon: Gauge, label: 'Overview', path: '/admin' },
        { icon: Airplane, label: 'Aircraft', path: '/admin/aircraft' },
        { icon: Users, label: 'Users', path: '/admin/users' },
        { icon: Wrench, label: 'Maintenance', path: '/admin/maintenance' },
        { icon: Target, label: 'Missions', path: '/admin/missions' },
        { icon: Siren, label: 'Emergencies', path: '/admin/emergencies' },
        { icon: FileText, label: 'Documents', path: '/admin/documents' },
        { icon: Gear, label: 'Settings', path: '/admin/settings' },
    ],
    PILOT: [
        { icon: Gauge, label: 'Overview', path: '/dashboard/pilot' },
        { icon: Airplane, label: 'Aircraft', path: '/dashboard/pilot/aircraft' },
        { icon: Target, label: 'Missions', path: '/dashboard/pilot/missions' },
        { icon: FileText, label: 'Documents', path: '/dashboard/pilot/documents' },
    ],
    TECHNICIAN: [
        { icon: Gauge, label: 'Overview', path: '/dashboard/technician' },
        { icon: Airplane, label: 'Aircraft', path: '/dashboard/technician/aircraft' },
        { icon: Wrench, label: 'Maintenance', path: '/dashboard/technician/maintenance' },
        { icon: ChartLineUp, label: 'Predictive', path: '/dashboard/technician/predictive-maintenance' },
        { icon: FileText, label: 'Documents', path: '/dashboard/technician/documents' },
    ],
    OPS_OFFICER: [
        { icon: Gauge, label: 'Overview', path: '/dashboard/ops' },
        { icon: Airplane, label: 'Aircraft', path: '/dashboard/ops/aircraft' },
        { icon: Wrench, label: 'Maintenance', path: '/dashboard/ops/maintenance' },
        { icon: Target, label: 'Missions', path: '/dashboard/ops/missions' },
        { icon: GlobeHemisphereWest, label: 'Live Map', path: '/dashboard/ops/live-map' },
        { icon: FileText, label: 'Documents', path: '/dashboard/ops/documents' },
    ],
    COMMANDER: [
        { icon: Gauge, label: 'Overview', path: '/dashboard/commander' },
        { icon: Airplane, label: 'Aircraft', path: '/dashboard/commander/aircraft' },
        { icon: Wrench, label: 'Maintenance', path: '/dashboard/commander/maintenance' },
        { icon: Target, label: 'Missions', path: '/dashboard/commander/missions' },
        { icon: GlobeHemisphereWest, label: 'Live Map', path: '/dashboard/ops/live-map' },
        { icon: Siren, label: 'Emergencies', path: '/dashboard/commander/emergencies' },
        { icon: FileText, label: 'Documents', path: '/dashboard/commander/documents' },
    ],
    EMERGENCY: [
        { icon: Gauge, label: 'Overview', path: '/dashboard/emergency' },
        { icon: Siren, label: 'Emergencies', path: '/dashboard/emergency/list' },
        { icon: FileText, label: 'Documents', path: '/dashboard/emergency/documents' },
    ],
    TRAINEE: [
        { icon: Gauge, label: 'Overview', path: '/dashboard/trainee' },
        { icon: GraduationCap, label: 'Training', path: '/dashboard/trainee/training' },
        { icon: FileText, label: 'Documents', path: '/dashboard/trainee/documents' },
    ],
    FAMILY: [
        { icon: Gauge, label: 'Overview', path: '/dashboard/family' },
        { icon: House, label: 'Welfare', path: '/dashboard/family/welfare' },
        { icon: FileText, label: 'Documents', path: '/dashboard/family/documents' },
    ],
};

export default function DashboardLayout({
    children,
    userRole = 'ADMIN',
    userName = 'User',
    userEmail = 'user@airbase.mil',
}: DashboardLayoutProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [chatOpen, setChatOpen] = useState(false);

    const handleLogout = () => {
        localStorage.removeItem('token');
        router.push('/');
    };

    const menuItems = menuItemsByRole[userRole] || menuItemsByRole.PILOT;

    return (
        <div className="min-h-screen bg-slate-950 flex">
            <div className="scanlines" />

            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-800 h-screen sticky top-0 flex flex-col">
                <div className="p-6 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                        <Airplane size={32} weight="duotone" className="text-blue-400" />
                        <div>
                            <h1 className="font-chivo font-bold text-sm uppercase tracking-wider">Mission Hub</h1>
                            <p className="text-xs text-slate-500 font-mono">{userRole.replace('_', ' ')}</p>
                        </div>
                    </div>
                </div>

                <nav className="flex-1 p-4">
                    <ul className="space-y-1">
                        {menuItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname === item.path;
                            return (
                                <li key={item.path}>
                                    <button
                                        onClick={() => router.push(item.path)}
                                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all duration-150 text-sm font-medium ${isActive
                                            ? 'text-blue-400 bg-blue-950/50 border-l-2 border-blue-400'
                                            : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
                                            }`}
                                        data-testid={`nav-${item.label.toLowerCase()}`}
                                    >
                                        <Icon size={20} weight="duotone" />
                                        {item.label}
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                </nav>

                <div className="p-4 border-t border-slate-800 space-y-2">
                    <button
                        onClick={() => setChatOpen(true)}
                        className="w-full flex items-center gap-3 px-3 py-2.5 text-blue-400 hover:text-blue-300 hover:bg-slate-800 rounded-sm transition-all duration-150 text-sm font-medium"
                        data-testid="open-chatbot-btn"
                    >
                        <Robot size={20} weight="duotone" />
                        AI Assistant
                    </button>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-3 py-2.5 text-red-400 hover:text-red-300 hover:bg-slate-800 rounded-sm transition-all duration-150 text-sm font-medium"
                        data-testid="logout-btn"
                    >
                        <SignOut size={20} />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                {/* Header */}
                <div className="backdrop-blur-md bg-slate-900/80 border-b border-slate-700 sticky top-0 z-40">
                    <div className="flex items-center justify-between px-6 py-4">
                        <div>
                            <h2 className="font-chivo font-bold text-xl uppercase tracking-wider">Mission Control</h2>
                            <p className="text-xs text-slate-400 font-mono mt-1">Welcome back, {userName}</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="text-right">
                                <p className="text-xs text-slate-500 uppercase tracking-wider font-mono">Logged in as</p>
                                <p className="text-sm font-mono text-slate-300">{userEmail}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Page Content */}
                <div className="p-6">
                    {children}
                </div>
            </main>

            <ChatBot isOpen={chatOpen} onClose={() => setChatOpen(false)} />
        </div>
    );
}
