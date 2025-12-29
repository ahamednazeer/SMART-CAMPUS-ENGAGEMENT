'use client';

import React from 'react';
import {
    ClipboardText,
    Phone,
    WarningCircle,
    Robot,
    FileText,
    Lightning
} from '@phosphor-icons/react';

interface QuickActionsProps {
    onOpenChecklist?: () => void;
    onContactOps?: () => void;
    onReportIssue?: () => void;
    onOpenAI?: () => void;
    onViewDocuments?: () => void;
}

export default function QuickActions({
    onOpenChecklist,
    onContactOps,
    onReportIssue,
    onOpenAI,
    onViewDocuments
}: QuickActionsProps) {
    const actions = [
        {
            id: 'checklist',
            label: 'Checklists',
            icon: ClipboardText,
            onClick: onOpenChecklist,
            color: 'hover:bg-blue-500/20 hover:border-blue-500/50 text-blue-400',
        },
        {
            id: 'contact',
            label: 'Contact Ops',
            icon: Phone,
            onClick: onContactOps,
            color: 'hover:bg-green-500/20 hover:border-green-500/50 text-green-400',
        },
        {
            id: 'report',
            label: 'Report Issue',
            icon: WarningCircle,
            onClick: onReportIssue,
            color: 'hover:bg-yellow-500/20 hover:border-yellow-500/50 text-yellow-400',
        },
        {
            id: 'documents',
            label: 'Documents',
            icon: FileText,
            onClick: onViewDocuments,
            color: 'hover:bg-purple-500/20 hover:border-purple-500/50 text-purple-400',
        },
        {
            id: 'ai',
            label: 'AI Assistant',
            icon: Robot,
            onClick: onOpenAI,
            color: 'hover:bg-cyan-500/20 hover:border-cyan-500/50 text-cyan-400',
        },
    ];

    return (
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-4">
            <div className="flex items-center gap-2 mb-3">
                <Lightning size={18} weight="duotone" className="text-blue-400" />
                <h4 className="text-slate-500 text-xs uppercase tracking-wider font-mono">Quick Actions</h4>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                {actions.map((action) => {
                    const Icon = action.icon;
                    return (
                        <button
                            key={action.id}
                            onClick={action.onClick}
                            className={`flex flex-col items-center gap-2 p-3 bg-slate-900/40 border border-slate-700/40 rounded-sm transition-all ${action.color}`}
                        >
                            <Icon size={24} weight="duotone" />
                            <span className="text-xs font-mono text-slate-300">{action.label}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
