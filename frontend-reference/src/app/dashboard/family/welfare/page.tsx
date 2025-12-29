'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { House, Phone, Heart, FirstAid } from '@phosphor-icons/react';

export default function FamilyWelfarePage() {
    const [resources, setResources] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await api.getWelfareResources();
            setResources(data);
        } catch (error) {
            console.error('Failed to load welfare resources:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="FAMILY" userName="Family Member" userEmail="family@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading welfare resources...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="FAMILY" userName="Family Member" userEmail="family@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Family Welfare & Support</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {resources.map((resource) => (
                        <div key={resource.id} className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6 hover:bg-slate-800/60 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-green-950/50 rounded-sm text-green-400">
                                    {resource.type === 'MEDICAL' ? <FirstAid size={24} weight="duotone" /> :
                                        resource.type === 'HOUSING' ? <House size={24} weight="duotone" /> :
                                            <Heart size={24} weight="duotone" />}
                                </div>
                                <span className="text-xs font-mono text-slate-500 uppercase tracking-wider border border-slate-700 px-2 py-1 rounded-sm">
                                    {resource.type}
                                </span>
                            </div>

                            <h4 className="text-lg font-bold text-slate-200 mb-2">{resource.title}</h4>
                            <p className="text-sm text-slate-400 mb-4">{resource.description}</p>

                            {resource.contactInfo && (
                                <div className="flex items-center gap-2 mt-auto pt-4 border-t border-slate-700/50 text-slate-300">
                                    <Phone size={16} weight="duotone" className="text-slate-500" />
                                    <span className="text-sm font-mono">{resource.contactInfo}</span>
                                </div>
                            )}
                        </div>
                    ))}

                    {resources.length === 0 && (
                        <div className="col-span-full py-12 text-center text-slate-500 font-mono bg-slate-800/20 border border-slate-800 rounded-sm">
                            <Heart size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
                            No welfare resources available at this time
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
