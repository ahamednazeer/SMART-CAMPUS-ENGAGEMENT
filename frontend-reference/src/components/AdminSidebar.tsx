'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    Users,
    Settings,
    FileText,
    Plane,
    LogOut,
    ShieldAlert
} from 'lucide-react';

const menuItems = [
    {
        title: 'Overview',
        href: '/admin',
        icon: LayoutDashboard
    },
    {
        title: 'User Management',
        href: '/admin/users',
        icon: Users
    },
    {
        title: 'Aircraft Fleet',
        href: '/admin/aircraft',
        icon: Plane
    },
    {
        title: 'Documents',
        href: '/admin/documents',
        icon: FileText
    },
    {
        title: 'System Settings',
        href: '/admin/settings',
        icon: Settings
    }
];

export default function AdminSidebar() {
    const pathname = usePathname();

    return (
        <div className="flex flex-col w-64 bg-slate-900 border-r border-slate-800 h-screen fixed left-0 top-0">
            <div className="p-6 border-b border-slate-800">
                <div className="flex items-center gap-2 text-emerald-500">
                    <ShieldAlert className="w-8 h-8" />
                    <span className="text-xl font-bold tracking-wider">AERO OPS</span>
                </div>
                <div className="mt-2 text-xs text-slate-500 font-mono">ADMINISTRATION CONSOLE</div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${isActive
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                                }`}
                        >
                            <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                            <span className="font-medium">{item.title}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-slate-800">
                <button
                    onClick={() => {
                        // Handle logout
                        localStorage.removeItem('token');
                        window.location.href = '/';
                    }}
                    className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                >
                    <LogOut className="w-5 h-5" />
                    <span className="font-medium">Sign Out</span>
                </button>
            </div>
        </div>
    );
}
