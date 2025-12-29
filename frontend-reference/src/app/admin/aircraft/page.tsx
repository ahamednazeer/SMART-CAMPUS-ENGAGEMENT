'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import DashboardLayout from '@/components/DashboardLayout';
import { Airplane, MagnifyingGlass, Wrench, Warning, Plus } from '@phosphor-icons/react';

export default function AircraftManagementPage() {
    const [aircraft, setAircraft] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchAircraft = async () => {
        try {
            const data = await api.getAircraft();
            setAircraft(data);
        } catch (error) {
            console.error('Failed to fetch aircraft:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAircraft();
    }, []);

    const filteredAircraft = aircraft.filter(ac =>
        ac.tailNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ac.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ac.squadron.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading fleet data...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Aircraft Fleet</h3>
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 px-4 py-2.5 border border-slate-700 text-slate-300 hover:bg-slate-800 rounded-sm font-medium tracking-wide uppercase text-sm transition-colors">
                            <Wrench size={16} weight="duotone" />
                            Maintenance
                        </button>
                        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150">
                            <Plus size={16} weight="bold" />
                            Add Aircraft
                        </button>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm flex items-center gap-4">
                        <div className="w-12 h-12 rounded-sm bg-green-950/50 border border-green-800 flex items-center justify-center text-green-400">
                            <Airplane size={24} weight="duotone" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold font-mono text-slate-100">{aircraft.filter(a => a.status === 'READY').length}</div>
                            <div className="text-xs text-slate-500 uppercase tracking-wider font-mono">Ready for Flight</div>
                        </div>
                    </div>
                    <div className="bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm flex items-center gap-4">
                        <div className="w-12 h-12 rounded-sm bg-yellow-950/50 border border-yellow-800 flex items-center justify-center text-yellow-400">
                            <Wrench size={24} weight="duotone" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold font-mono text-slate-100">{aircraft.filter(a => a.status === 'IN_MAINTENANCE').length}</div>
                            <div className="text-xs text-slate-500 uppercase tracking-wider font-mono">In Maintenance</div>
                        </div>
                    </div>
                    <div className="bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm flex items-center gap-4">
                        <div className="w-12 h-12 rounded-sm bg-red-950/50 border border-red-800 flex items-center justify-center text-red-400">
                            <Warning size={24} weight="duotone" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold font-mono text-slate-100">{aircraft.filter(a => a.status === 'GROUNDED').length}</div>
                            <div className="text-xs text-slate-500 uppercase tracking-wider font-mono">Grounded</div>
                        </div>
                    </div>
                </div>

                {/* Search */}
                <div className="flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm">
                    <MagnifyingGlass className="text-slate-500" size={20} />
                    <input
                        type="text"
                        placeholder="Search fleet by tail number, type, or squadron..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-transparent border-none focus:outline-none text-slate-200 w-full placeholder-slate-500 font-mono text-sm"
                    />
                </div>

                {/* Fleet Table */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Tail Number</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Squadron</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Location</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Maintenance</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Flight Hours</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {filteredAircraft.map((ac) => (
                                    <tr key={ac.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-sm bg-blue-950/50 border border-blue-800 flex items-center justify-center text-blue-400">
                                                    <Airplane size={20} weight="duotone" />
                                                </div>
                                                <div>
                                                    <div className="font-bold font-mono text-slate-200">{ac.tailNumber}</div>
                                                    <div className="text-xs text-slate-500">{ac.type}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4"><StatusBadge status={ac.status} /></td>
                                        <td className="px-6 py-4 text-sm text-slate-400">{ac.squadron}</td>
                                        <td className="px-6 py-4 text-sm text-slate-400">{ac.location}</td>
                                        <td className="px-6 py-4">
                                            <div className="text-xs font-mono">
                                                <div className="text-slate-400">Last: {new Date(ac.lastMaintenance).toLocaleDateString()}</div>
                                                <div className={`mt-0.5 ${new Date(ac.nextMaintenance) < new Date() ? 'text-red-400' : 'text-slate-500'}`}>
                                                    Next: {new Date(ac.nextMaintenance).toLocaleDateString()}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-sm text-slate-300">{ac.flightHours.toFixed(1)}</td>
                                    </tr>
                                ))}
                                {filteredAircraft.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            No aircraft found.
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
