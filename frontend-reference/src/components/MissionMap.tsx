'use client';

import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import io, { Socket } from 'socket.io-client';
import { Airplane, NavigationArrow } from '@phosphor-icons/react';

// Fix Leaflet icon issue in Next.js
const iconPerson = new L.Icon({
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Custom Aircraft Icon
const createAircraftIcon = (heading: number) => {
    return L.divIcon({
        className: 'custom-aircraft-icon',
        html: `<div style="transform: rotate(${heading}deg); color: #3b82f6; font-size: 24px;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 256 256"><path d="M245.42,118.88l-128-88a8,8,0,0,0-10.84,2.2l-32,48L32.19,69.56A16,16,0,0,0,8,82.85V96a8,8,0,0,0,8,8h64v64H48a8,8,0,0,0-8,8v16a8,8,0,0,0,8,8H128a8,8,0,0,0,8-8V176a8,8,0,0,0-8-8H96V104h.09l38.31-57.46,106.78,73.41a8,8,0,0,0,4.24,11.05Z"></path></svg>
               </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    });
};

interface TelemetryData {
    missionId: string;
    aircraftId: string;
    tailNumber: string;
    type: string;
    latitude: number;
    longitude: number;
    altitude: number;
    speed: number;
    heading: number;
}

export default function MissionMap() {
    const [telemetry, setTelemetry] = useState<Record<string, TelemetryData>>({});
    const socketRef = useRef<Socket | null>(null);

    useEffect(() => {
        // Connect to WebSocket
        socketRef.current = io('http://localhost:4000');

        socketRef.current.on('connect', () => {
            console.log('Connected to WebSocket server');
        });

        socketRef.current.on('telemetry:update', (data: TelemetryData[]) => {
            setTelemetry(prev => {
                const next = { ...prev };
                data.forEach(item => {
                    next[item.aircraftId] = item;
                });
                return next;
            });
        });

        return () => {
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
        };
    }, []);

    // Default center (can be adjusted)
    const center: [number, number] = [30.0, -90.0]; // Example: US Gulf Coast

    return (
        <div className="h-[600px] w-full rounded-sm overflow-hidden border border-slate-800 relative z-0">
            <MapContainer center={center} zoom={5} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {Object.values(telemetry).map((ac) => (
                    <Marker
                        key={ac.aircraftId}
                        position={[ac.latitude, ac.longitude]}
                        icon={createAircraftIcon(ac.heading)}
                    >
                        <Popup className="custom-popup">
                            <div className="p-2 min-w-[200px]">
                                <h3 className="font-bold text-slate-900 flex items-center gap-2">
                                    <Airplane size={16} weight="duotone" />
                                    {ac.tailNumber}
                                </h3>
                                <div className="text-xs text-slate-600 mt-1 space-y-1 font-mono">
                                    <p>Type: {ac.type}</p>
                                    <p>Alt: {Math.round(ac.altitude)} ft</p>
                                    <p>Spd: {Math.round(ac.speed)} kts</p>
                                    <p>Hdg: {Math.round(ac.heading)}°</p>
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>

            {/* Legend / Overlay */}
            <div className="absolute top-4 right-4 z-[1000] bg-slate-900/90 backdrop-blur border border-slate-700 p-3 rounded-sm shadow-xl">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-2">
                    <NavigationArrow className="text-blue-400" />
                    Live Traffic
                </h4>
                <div className="text-xs text-slate-400 font-mono">
                    Active Aircraft: <span className="text-white font-bold">{Object.keys(telemetry).length}</span>
                </div>
            </div>
        </div>
    );
}
