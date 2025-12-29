'use client';

import React, { ReactNode } from 'react';

interface DataCardProps {
    title: string;
    value: string | number;
    icon?: React.ElementType;
    className?: string;
    children?: ReactNode;
}

export function DataCard({ title, value, icon: Icon, className = '', children }: DataCardProps) {
    return (
        <div
            className={`bg-slate-800/40 border border-slate-700/60 rounded-sm p-4 relative overflow-hidden hover:border-slate-500 transition-colors duration-200 ${className}`}
            data-testid="data-card"
        >
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-slate-500 text-[10px] uppercase tracking-wider font-mono mb-1">
                        {title}
                    </p>
                    <p className="text-3xl font-bold font-mono text-slate-100">{value}</p>
                </div>
                {Icon && <Icon className="text-slate-600" size={48} weight="duotone" />}
            </div>
            {children && <div className="mt-3">{children}</div>}
        </div>
    );
}

export default DataCard;
