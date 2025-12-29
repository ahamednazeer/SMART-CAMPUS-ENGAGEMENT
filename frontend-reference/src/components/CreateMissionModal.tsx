'use client';

import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { api } from '@/lib/api';

interface CreateMissionModalProps {
    onClose: () => void;
    onSuccess: () => void;
}

export default function CreateMissionModal({ onClose, onSuccess }: CreateMissionModalProps) {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        type: 'TRAINING',
        aircraftId: '',
        pilotId: '',
        startTime: '',
        endTime: '',
        destinationName: '',
        destinationLat: '',
        destinationLon: '',
    });
    const [aircraft, setAircraft] = useState<any[]>([]);
    const [pilots, setPilots] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        loadResources();
    }, []);

    const loadResources = async () => {
        try {
            const [aircraftData, usersData] = await Promise.all([
                api.getAircraft(),
                api.getAllUsers(),
            ]);
            setAircraft(aircraftData.filter((a: any) => a.status === 'READY'));
            setPilots(usersData.filter((u: any) => u.role === 'PILOT'));
        } catch (err) {
            console.error('Failed to load resources', err);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await api.createMission({
                ...formData,
                startTime: new Date(formData.startTime).toISOString(),
                endTime: formData.endTime ? new Date(formData.endTime).toISOString() : undefined,
                destinationLat: formData.destinationLat ? parseFloat(formData.destinationLat) : undefined,
                destinationLon: formData.destinationLon ? parseFloat(formData.destinationLon) : undefined,
            });
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.message || 'Failed to create mission');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-surface-elevated p-6 rounded-lg w-full max-w-md border border-border">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold text-primary">Create Mission</h2>
                    <button onClick={onClose} className="text-secondary hover:text-primary">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {error && (
                    <div className="bg-critical/20 text-critical p-3 rounded mb-4 text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-secondary mb-1">Mission Title</label>
                        <input
                            type="text"
                            required
                            className="w-full bg-surface border border-border rounded p-2 text-primary"
                            value={formData.title}
                            onChange={e => setFormData({ ...formData, title: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-secondary mb-1">Type</label>
                        <select
                            className="w-full bg-surface border border-border rounded p-2 text-primary"
                            value={formData.type}
                            onChange={e => setFormData({ ...formData, type: e.target.value })}
                        >
                            <option value="TRAINING">Training</option>
                            <option value="PATROL">Patrol</option>
                            <option value="TRANSPORT">Transport</option>
                            <option value="MAINTENANCE_FERRY">Maintenance Ferry</option>
                            <option value="SEARCH_AND_RESCUE">Search & Rescue</option>
                            <option value="OTHER">Other</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-secondary mb-1">Aircraft</label>
                        <select
                            className="w-full bg-surface border border-border rounded p-2 text-primary"
                            value={formData.aircraftId}
                            required
                            onChange={e => setFormData({ ...formData, aircraftId: e.target.value })}
                        >
                            <option value="">Select Aircraft</option>
                            {aircraft.map(a => (
                                <option key={a.id} value={a.id}>{a.tailNumber} ({a.type})</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-secondary mb-1">Pilot</label>
                        <select
                            className="w-full bg-surface border border-border rounded p-2 text-primary"
                            value={formData.pilotId}
                            required
                            onChange={e => setFormData({ ...formData, pilotId: e.target.value })}
                        >
                            <option value="">Select Pilot</option>
                            {pilots.map(p => (
                                <option key={p.id} value={p.id}>{p.firstName} {p.lastName}</option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-secondary mb-1">Start Time</label>
                            <input
                                type="datetime-local"
                                required
                                className="w-full bg-surface border border-border rounded p-2 text-primary"
                                value={formData.startTime}
                                onChange={e => setFormData({ ...formData, startTime: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-secondary mb-1">End Time</label>
                            <input
                                type="datetime-local"
                                className="w-full bg-surface border border-border rounded p-2 text-primary"
                                value={formData.endTime}
                                onChange={e => setFormData({ ...formData, endTime: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <div className="col-span-3">
                            <label className="block text-sm font-medium text-secondary mb-1">Destination Name</label>
                            <input
                                type="text"
                                className="w-full bg-surface border border-border rounded p-2 text-primary"
                                value={formData.destinationName}
                                onChange={e => setFormData({ ...formData, destinationName: e.target.value })}
                                placeholder="e.g. Chennai Air Base"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-secondary mb-1">Lat</label>
                            <input
                                type="number"
                                step="any"
                                className="w-full bg-surface border border-border rounded p-2 text-primary"
                                value={formData.destinationLat}
                                onChange={e => setFormData({ ...formData, destinationLat: e.target.value })}
                                placeholder="13.0827"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-secondary mb-1">Lon</label>
                            <input
                                type="number"
                                step="any"
                                className="w-full bg-surface border border-border rounded p-2 text-primary"
                                value={formData.destinationLon}
                                onChange={e => setFormData({ ...formData, destinationLon: e.target.value })}
                                placeholder="80.2707"
                            />
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-secondary hover:text-primary"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
                        >
                            {loading ? 'Creating...' : 'Create Mission'}
                        </button>
                    </div>
                </form>
            </div >
        </div >
    );
}
