'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { StatusBadge } from '@/components/StatusBadge';
import { Airplane, MagnifyingGlass } from '@phosphor-icons/react';
import { Aircraft } from '@/types';

export default function CommanderAircraftPage() {
    const [aircraft, setAircraft] = useState<Aircraft[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await api.getAircraft();
            setAircraft(data);
        } catch (error) {
            console.error('Failed to load aircraft:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredAircraft = aircraft.filter(ac =>
        ac.tailNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ac.type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <DashboardLayout userRole="COMMANDER" userName="Commander" userEmail="commander@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading aircraft...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="COMMANDER" userName="Commander" userEmail="commander@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Fleet Overview</h3>

                <div className="flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm">
                    <MagnifyingGlass className="text-slate-500" size={20} />
                    <input
                        type="text"
                        placeholder="Search aircraft..."
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
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Tail Number</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Squadron</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Flight Hours</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Location</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {filteredAircraft.map((ac) => (
                                    <tr key={ac.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{ac.tailNumber}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{ac.type}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{ac.squadron}</td>
                                        <td className="px-6 py-4"><StatusBadge status={ac.status} /></td>
                                        <td className="px-6 py-4 font-mono text-sm">{ac.flightHours.toFixed(1)} hrs</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{ac.location}</td>
                                    </tr>
                                ))}
                                {filteredAircraft.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            <Airplane size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
                                            No aircraft found
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
