'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { GlobeHemisphereWest } from '@phosphor-icons/react';

// Dynamically import map to avoid SSR issues with Leaflet
const MissionMap = dynamic(() => import('@/components/MissionMap'), {
    ssr: false,
    loading: () => (
        <div className="h-[600px] w-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 font-mono animate-pulse">
            Initializing Satellite Link...
        </div>
    ),
});

export default function LiveMapPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-100 font-chivo uppercase tracking-wide flex items-center gap-3">
                        <GlobeHemisphereWest className="text-blue-400" />
                        Live Mission Map
                    </h1>
                    <p className="text-slate-400 text-sm font-mono mt-1">Real-time global asset tracking</p>
                </div>
            </div>

            <MissionMap />
        </div>
    );
}
