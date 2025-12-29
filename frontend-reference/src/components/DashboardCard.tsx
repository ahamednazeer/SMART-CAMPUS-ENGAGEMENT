import React, { ReactNode } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface DashboardCardProps {
    title: string;
    value: string | number;
    change?: {
        value: number;
        label: string;
    };
    icon?: ReactNode;
    children?: ReactNode;
    className?: string;
    variant?: 'default' | 'pilot' | 'technician' | 'commander' | 'admin';
}

export default function DashboardCard({
    title,
    value,
    change,
    icon,
    children,
    className = '',
    variant = 'default',
}: DashboardCardProps) {
    const variantClasses = {
        default: '',
        pilot: 'gradient-pilot border-pilot/20',
        technician: 'gradient-technician border-technician/20',
        commander: 'gradient-commander border-commander/20',
        admin: 'gradient-admin border-admin/20',
    };

    return (
        <div
            className={`
                glass rounded-xl p-6 
                transition-all duration-300 
                hover:shadow-xl hover:-translate-y-1 
                hover:border-pilot/30
                group
                ${variantClasses[variant]}
                ${className}
            `}
        >
            <div className="flex items-start justify-between mb-4">
                <h3 className="text-secondary text-sm font-medium uppercase tracking-wide">
                    {title}
                </h3>
                {icon && (
                    <div className="text-secondary transition-all duration-300 group-hover:text-pilot group-hover:scale-110">
                        {icon}
                    </div>
                )}
            </div>

            <div className="mb-2">
                <div className="text-4xl font-bold text-primary transition-all duration-300 group-hover:text-pilot">
                    {value}
                </div>
            </div>

            {change && (
                <div className="flex items-center gap-1 text-sm">
                    {change.value > 0 ? (
                        <>
                            <TrendingUp className="w-4 h-4 text-success animate-pulse-glow" />
                            <span className="text-success font-semibold">+{change.value}</span>
                        </>
                    ) : change.value < 0 ? (
                        <>
                            <TrendingDown className="w-4 h-4 text-critical animate-pulse-glow" />
                            <span className="text-critical font-semibold">{change.value}</span>
                        </>
                    ) : null}
                    <span className="text-muted ml-1">{change.label}</span>
                </div>
            )}

            {children && (
                <div className="mt-4 pt-4 border-t border-border/50">
                    {children}
                </div>
            )}
        </div>
    );
}
