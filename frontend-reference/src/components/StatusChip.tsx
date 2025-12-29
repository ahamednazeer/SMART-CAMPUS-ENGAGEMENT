import React from 'react';
import { AircraftStatus, MaintenanceStatus, EmergencyStatus } from '@/types';

type StatusVariant =
    | AircraftStatus
    | MaintenanceStatus
    | EmergencyStatus
    | 'CRITICAL'
    | 'HIGH'
    | 'MEDIUM'
    | 'LOW';

interface StatusChipProps {
    status: StatusVariant;
    size?: 'sm' | 'md' | 'lg';
    animated?: boolean;
}

const statusConfig: Record<string, { bg: string; text: string; border: string; glow: string; label?: string }> = {
    // Aircraft statuses
    READY: {
        bg: 'bg-success/10',
        text: 'text-success',
        border: 'border-success/30',
        glow: 'hover:shadow-success/20'
    },
    IN_MAINTENANCE: {
        bg: 'bg-warning/10',
        text: 'text-warning',
        border: 'border-warning/30',
        glow: 'hover:shadow-warning/20'
    },
    GROUNDED: {
        bg: 'bg-critical/10',
        text: 'text-critical',
        border: 'border-critical/30',
        glow: 'hover:shadow-critical/20'
    },
    IN_FLIGHT: {
        bg: 'bg-info/10',
        text: 'text-info',
        border: 'border-info/30',
        glow: 'hover:shadow-info/20'
    },

    // Maintenance statuses
    PENDING: {
        bg: 'bg-warning/10',
        text: 'text-warning',
        border: 'border-warning/30',
        glow: 'hover:shadow-warning/20'
    },
    IN_PROGRESS: {
        bg: 'bg-info/10',
        text: 'text-info',
        border: 'border-info/30',
        glow: 'hover:shadow-info/20'
    },
    COMPLETED: {
        bg: 'bg-success/10',
        text: 'text-success',
        border: 'border-success/30',
        glow: 'hover:shadow-success/20'
    },
    CANCELLED: {
        bg: 'bg-text-muted/10',
        text: 'text-muted',
        border: 'border-text-muted/30',
        glow: 'hover:shadow-text-muted/20'
    },

    // Emergency statuses
    ACTIVE: {
        bg: 'bg-critical/10',
        text: 'text-critical',
        border: 'border-critical/30',
        glow: 'hover:shadow-critical/20'
    },
    RESOLVING: {
        bg: 'bg-warning/10',
        text: 'text-warning',
        border: 'border-warning/30',
        glow: 'hover:shadow-warning/20'
    },

    // Priority levels
    CRITICAL: {
        bg: 'bg-critical/10',
        text: 'text-critical',
        border: 'border-critical/30',
        glow: 'hover:shadow-critical/20'
    },
    HIGH: {
        bg: 'bg-warning/10',
        text: 'text-warning',
        border: 'border-warning/30',
        glow: 'hover:shadow-warning/20'
    },
    MEDIUM: {
        bg: 'bg-info/10',
        text: 'text-info',
        border: 'border-info/30',
        glow: 'hover:shadow-info/20'
    },
    LOW: {
        bg: 'bg-text-muted/10',
        text: 'text-muted',
        border: 'border-text-muted/30',
        glow: 'hover:shadow-text-muted/20'
    },
};

const sizeClasses = {
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
};

export default function StatusChip({ status, size = 'md', animated = true }: StatusChipProps) {
    const config = statusConfig[status] || {
        bg: 'bg-text-muted/10',
        text: 'text-muted',
        border: 'border-text-muted/30',
        glow: 'hover:shadow-text-muted/20'
    };
    const label = config.label || status.replace(/_/g, ' ');

    const shouldPulse = animated && (status === 'ACTIVE' || status === 'IN_PROGRESS' || status === 'IN_FLIGHT');

    return (
        <span
            className={`
                inline-flex items-center justify-center
                rounded-full font-semibold uppercase tracking-wide
                border backdrop-blur-sm
                transition-all duration-300
                ${config.bg} ${config.text} ${config.border} ${config.glow}
                ${sizeClasses[size]}
                ${shouldPulse ? 'animate-pulse-glow' : ''}
                hover:scale-105 hover:shadow-lg
            `}
        >
            {shouldPulse && (
                <span className="w-1.5 h-1.5 rounded-full bg-current mr-2 animate-pulse-glow" />
            )}
            {label}
        </span>
    );
}
