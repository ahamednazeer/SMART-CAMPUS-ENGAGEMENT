'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { StatusBadge } from '@/components/StatusBadge';
import { Airplane, MagnifyingGlass } from '@phosphor-icons/react';
import { Aircraft } from '@/types';

export default function TechnicianAircraftPage() {
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

    const handleStatusUpdate = async (id: string, status: string) => {
        try {
            await api.updateAircraft(id, { status });
            loadData();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    };

    const filteredAircraft = aircraft.filter(ac =>
        ac.tailNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ac.type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <DashboardLayout userRole="TECHNICIAN" userName="Technician" userEmail="tech@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading aircraft...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="TECHNICIAN" userName="Technician" userEmail="tech@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Aircraft Maintenance</h3>

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
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {filteredAircraft.map((ac) => (
                                    <tr key={ac.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{ac.tailNumber}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{ac.type}</td>
                                        <td className="px-6 py-4"><StatusBadge status={ac.status} /></td>
                                        <td className="px-6 py-4">
                                            <div className="flex gap-2">
                                                {ac.status !== 'READY' && (
                                                    <button
                                                        onClick={() => handleStatusUpdate(ac.id, 'READY')}
                                                        className="px-2 py-1 text-xs bg-green-950/50 text-green-400 border border-green-800 rounded-sm hover:bg-green-900/50 font-mono uppercase tracking-wider"
                                                    >
                                                        Mark Ready
                                                    </button>
                                                )}
                                                {ac.status !== 'IN_MAINTENANCE' && (
                                                    <button
                                                        onClick={() => handleStatusUpdate(ac.id, 'IN_MAINTENANCE')}
                                                        className="px-2 py-1 text-xs bg-yellow-950/50 text-yellow-400 border border-yellow-800 rounded-sm hover:bg-yellow-900/50 font-mono uppercase tracking-wider"
                                                    >
                                                        Start Maint.
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {filteredAircraft.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-12 text-center text-slate-500 font-mono">
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
