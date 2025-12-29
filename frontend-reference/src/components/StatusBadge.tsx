'use client';

import React from 'react';

interface StatusBadgeProps {
    status: string;
}

const getStatusColor = (status: string): string => {
    const statusUpper = status.toUpperCase();
    switch (statusUpper) {
        case 'READY':
        case 'COMPLETED':
        case 'ACTIVE':
        case 'OPEN':
            return 'text-green-400 bg-green-950/50 border-green-800';
        case 'IN_MAINTENANCE':
        case 'PENDING':
        case 'PLANNED':
        case 'MAINTENANCE':
            return 'text-yellow-400 bg-yellow-950/50 border-yellow-800';
        case 'GROUNDED':
        case 'CANCELLED':
        case 'CLOSED':
        case 'ERROR':
            return 'text-red-400 bg-red-950/50 border-red-800';
        case 'IN_PROGRESS':
        case 'IN_FLIGHT':
            return 'text-blue-400 bg-blue-950/50 border-blue-800';
        default:
            return 'text-slate-400 bg-slate-800/50 border-slate-700';
    }
};

export function StatusBadge({ status }: StatusBadgeProps) {
    return (
        <span
            className={`font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border ${getStatusColor(status)}`}
            data-testid={`status-badge-${status.toLowerCase()}`}
        >
            {status.replace(/_/g, ' ')}
        </span>
    );
}

export default StatusBadge;
