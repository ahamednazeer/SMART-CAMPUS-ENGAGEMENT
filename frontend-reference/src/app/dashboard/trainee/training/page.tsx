'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { GraduationCap, BookOpen, CheckCircle } from '@phosphor-icons/react';

export default function TraineeTrainingPage() {
    const [modules, setModules] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await api.getTrainingModules();
            setModules(data);
        } catch (error) {
            console.error('Failed to load training modules:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="TRAINEE" userName="Trainee" userEmail="trainee@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading training modules...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="TRAINEE" userName="Trainee" userEmail="trainee@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Training Modules</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {modules.map((module) => (
                        <div key={module.id} className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6 hover:bg-slate-800/60 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-blue-950/50 rounded-sm text-blue-400">
                                    <BookOpen size={24} weight="duotone" />
                                </div>
                                {module.completed && (
                                    <div className="flex items-center gap-2 text-green-400 text-xs font-mono uppercase tracking-wider">
                                        <CheckCircle size={16} weight="fill" />
                                        Completed
                                    </div>
                                )}
                            </div>

                            <h4 className="text-lg font-bold text-slate-200 mb-2">{module.title}</h4>
                            <p className="text-sm text-slate-400 mb-4 line-clamp-2">{module.description}</p>

                            <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-700/50">
                                <span className="text-xs font-mono text-slate-500">
                                    Duration: {module.duration}m
                                </span>
                                <button className="text-sm text-blue-400 hover:text-blue-300 font-medium transition-colors">
                                    {module.completed ? 'Review' : 'Start Module'} &rarr;
                                </button>
                            </div>
                        </div>
                    ))}

                    {modules.length === 0 && (
                        <div className="col-span-full py-12 text-center text-slate-500 font-mono bg-slate-800/20 border border-slate-800 rounded-sm">
                            <GraduationCap size={48} weight="duotone" className="mx-auto mb-4 opacity-50" />
                            No training modules assigned
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
