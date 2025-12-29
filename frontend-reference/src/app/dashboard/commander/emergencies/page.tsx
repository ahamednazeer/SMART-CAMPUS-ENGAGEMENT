'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { StatusBadge } from '@/components/StatusBadge';
import { Siren, MagnifyingGlass } from '@phosphor-icons/react';

export default function CommanderEmergenciesPage() {
    const [emergencies, setEmergencies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await api.getEmergencies();
            setEmergencies(data);
        } catch (error) {
            console.error('Failed to load emergencies:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredEmergencies = emergencies.filter(e =>
        e.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <DashboardLayout userRole="COMMANDER" userName="Commander" userEmail="commander@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading emergencies...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="COMMANDER" userName="Commander" userEmail="commander@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Emergency Reports</h3>

                <div className="flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm">
                    <MagnifyingGlass className="text-slate-500" size={20} />
                    <input
                        type="text"
                        placeholder="Search emergencies..."
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
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Description</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Priority</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Reported</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {filteredEmergencies.map((emergency) => (
                                    <tr key={emergency.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-sm">{emergency.type}</td>
                                        <td className="px-6 py-4 text-sm text-slate-300">{emergency.description}</td>
                                        <td className="px-6 py-4"><StatusBadge status={emergency.priority || 'HIGH'} /></td>
                                        <td className="px-6 py-4"><StatusBadge status={emergency.status} /></td>
                                        <td className="px-6 py-4 font-mono text-sm">{new Date(emergency.createdAt).toLocaleString()}</td>
                                    </tr>
                                ))}
                                {filteredEmergencies.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            <Siren size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
                                            No active emergencies
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
