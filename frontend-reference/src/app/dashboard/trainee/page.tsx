'use client';

import React, { useEffect, useState } from 'react';
import { GraduationCap, BookOpen, Trophy, Clock, CheckCircle } from '@phosphor-icons/react';
import DashboardLayout from '@/components/DashboardLayout';
import { DataCard } from '@/components/DataCard';
import { api } from '@/lib/api';

interface TrainingModule {
    id: string;
    title: string;
    description: string;
    duration: number;
    category: string;
}

interface TrainingProgress {
    id: string;
    moduleId: string;
    completed: boolean;
    score?: number;
    startedAt: string;
    completedAt?: string;
    module: TrainingModule;
}

interface DashboardData {
    modules: TrainingModule[];
    progress: TrainingProgress[];
    stats: {
        completed: number;
        total: number;
        percentage: number;
    };
}

export default function TraineeDashboard() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const dashboardData = await api.getTraineeDashboard();
            setData(dashboardData);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        } finally {
            setLoading(false);
        }
    };

    const getModuleProgress = (moduleId: string) => {
        return data?.progress.find(p => p.moduleId === moduleId);
    };

    const handleStartModule = async (moduleId: string) => {
        try {
            await api.updateTrainingProgress(moduleId, false);
            loadData();
        } catch (error) {
            console.error('Failed to start module:', error);
        }
    };

    const handleCompleteModule = async (moduleId: string) => {
        try {
            await api.updateTrainingProgress(moduleId, true, 100);
            loadData();
        } catch (error) {
            console.error('Failed to complete module:', error);
        }
    };

    if (loading) {
        return (
            <DashboardLayout userRole="TRAINEE" userName="Trainee" userEmail="trainee@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="TRAINEE" userName="Trainee" userEmail="trainee@airbase.mil">
            <div className="space-y-6">
                <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">Training Center</h3>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <DataCard
                        title="Total Modules"
                        value={data?.stats.total || 0}
                        icon={BookOpen}
                    >
                        <div className="text-xs text-blue-400 font-mono">Available courses</div>
                    </DataCard>

                    <DataCard
                        title="Completed"
                        value={data?.stats.completed || 0}
                        icon={CheckCircle}
                    >
                        <div className="text-xs text-green-400 font-mono">Finished modules</div>
                    </DataCard>

                    <DataCard
                        title="In Progress"
                        value={(data?.stats.total || 0) - (data?.stats.completed || 0)}
                        icon={Clock}
                    >
                        <div className="text-xs text-yellow-400 font-mono">Remaining</div>
                    </DataCard>

                    <DataCard
                        title="Progress"
                        value={`${data?.stats.percentage || 0}%`}
                        icon={Trophy}
                    >
                        <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
                            <div
                                className="bg-blue-500 h-2 rounded-full transition-all"
                                style={{ width: `${data?.stats.percentage || 0}%` }}
                            />
                        </div>
                    </DataCard>
                </div>

                {/* Training Modules */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-2">
                        <GraduationCap className="text-blue-400" size={20} />
                        <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Training Modules</h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
                        {data?.modules.map((module) => {
                            const progress = getModuleProgress(module.id);
                            const isCompleted = progress?.completed;
                            const isStarted = !!progress;

                            return (
                                <div
                                    key={module.id}
                                    className={`bg-slate-900/50 border rounded-sm p-4 ${isCompleted
                                            ? 'border-green-800/50'
                                            : isStarted
                                                ? 'border-yellow-800/50'
                                                : 'border-slate-700'
                                        }`}
                                >
                                    <div className="flex items-start justify-between mb-2">
                                        <h5 className="font-semibold text-slate-100">{module.title}</h5>
                                        {isCompleted && (
                                            <CheckCircle className="text-green-500" size={20} weight="fill" />
                                        )}
                                    </div>
                                    <p className="text-sm text-slate-400 mb-3">{module.description}</p>
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-slate-500 font-mono">
                                            <Clock size={14} className="inline mr-1" />
                                            {module.duration} min
                                        </span>
                                        <span className="text-slate-500 font-mono uppercase">
                                            {module.category}
                                        </span>
                                    </div>
                                    <div className="mt-4">
                                        {isCompleted ? (
                                            <div className="text-green-400 text-xs font-mono text-center py-2">
                                                ✓ Completed {progress.score ? `- Score: ${progress.score}%` : ''}
                                            </div>
                                        ) : isStarted ? (
                                            <button
                                                onClick={() => handleCompleteModule(module.id)}
                                                className="w-full px-3 py-2 text-xs bg-green-950/50 text-green-400 border border-green-800 rounded-sm hover:bg-green-900/50 font-mono uppercase tracking-wider"
                                            >
                                                Mark Complete
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => handleStartModule(module.id)}
                                                className="w-full px-3 py-2 text-xs bg-blue-950/50 text-blue-400 border border-blue-800 rounded-sm hover:bg-blue-900/50 font-mono uppercase tracking-wider"
                                            >
                                                Start Module
                                            </button>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                        {(!data?.modules || data.modules.length === 0) && (
                            <div className="col-span-full text-center py-12 text-slate-500 font-mono">
                                No training modules available
                            </div>
                        )}
                    </div>
                </div>

                {/* AI Training Assistant Hint */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-6">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-blue-950/50 border border-blue-800 flex items-center justify-center">
                            <GraduationCap className="text-blue-400" size={24} />
                        </div>
                        <div>
                            <h4 className="font-semibold text-slate-100">Training AI Assistant</h4>
                            <p className="text-sm text-slate-400">
                                Use the AI chatbot (bottom right) to ask questions about training materials and procedures.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
