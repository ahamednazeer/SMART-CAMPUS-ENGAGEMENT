'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import {
    Sparkle,
    Users,
    CheckCircle,
    Funnel,
    Pulse,
    ArrowLeft
} from '@phosphor-icons/react';

interface HostelDetails {
    id: number;
    name: string;
    address: string | null;
    capacity: number;
    room_count: number;
    occupied_beds: number;
}

interface Recommendation {
    student_id: number;
    student_name: string;
    student_register_number: string | null;
    department: string | null;
    study_year: number | null;
    degree: string | null;
    batch: string | null;
    gender: string | null;
    hostel_id: number;
    room_id: number;
    room_number: string;
    room_floor: number | null;
    score: number;
}

interface AutoAssignPreview {
    hostel_id: number;
    recommended_count: number;
    skipped_count: number;
    recommendations: Recommendation[];
    skipped: { student_id: number; reason: string }[];
}

interface AutoAssignResult {
    hostel_id: number;
    assigned_count: number;
    skipped_count: number;
    created_by_id?: number | null;
    created_by_name?: string | null;
    created_by_username?: string | null;
    created_by_email?: string | null;
    created_at?: string | null;
    assigned: {
        student_id: number;
        student_name: string;
        student_register_number: string | null;
        room_number: string;
        room_floor: number | null;
        assigned_at: string;
    }[];
    skipped: { student_id: number; reason: string }[];
}

interface UnassignedHosteller {
    student_id: number;
    student_name: string;
    student_register_number: string | null;
    student_email: string | null;
    student_department: string | null;
    student_batch: string | null;
    student_degree: string | null;
    student_study_year: number | null;
    student_gender: string | null;
}

export default function HostelAutoAssignPage() {
    const router = useRouter();
    const [hostels, setHostels] = useState<HostelDetails[]>([]);
    const [hostel, setHostel] = useState<HostelDetails | null>(null);
    const [selectedHostelId, setSelectedHostelId] = useState<number | null>(null);
    const [unassigned, setUnassigned] = useState<UnassignedHosteller[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingUnassigned, setLoadingUnassigned] = useState(false);
    const [preview, setPreview] = useState<AutoAssignPreview | null>(null);
    const [lastResult, setLastResult] = useState<AutoAssignResult | null>(null);
    const [generating, setGenerating] = useState(false);
    const [confirming, setConfirming] = useState(false);
    const [exporting, setExporting] = useState<'excel' | 'pdf' | null>(null);
    const [selected, setSelected] = useState<Set<number>>(new Set());

    const [filters, setFilters] = useState({
        department: '',
        study_year: '',
        degree: '',
        batch: '',
        gender: '',
        limit: '',
        strategy: 'fill',
    });

    useEffect(() => {
        initializePage();
    }, []);

    async function initializePage() {
        setLoading(true);
        try {
            const assignedHostels = await api.getWardenHostels();
            const hostelList: HostelDetails[] = assignedHostels || [];
            setHostels(hostelList);
            if (hostelList.length === 0) {
                setHostel(null);
                return;
            }

            const defaultHostelId = hostelList[0].id;
            setSelectedHostelId(defaultHostelId);
            await loadHostelScopedData(defaultHostelId);
        } catch (err) {
            console.error('Failed to initialize auto-assign page', err);
        } finally {
            setLoading(false);
        }
    }

    async function loadHostelScopedData(hostelId: number) {
        if (!hostelId) return;
        const [hostelData, unassignedData, latest] = await Promise.all([
            api.getWardenHostel(hostelId),
            api.getWardenUnassignedHostellers(hostelId),
            api.getLatestAutoAssignResult(hostelId).catch(() => null),
        ]);
        setHostel(hostelData);
        setUnassigned(unassignedData || []);
        setLastResult(latest || null);
    }

    async function fetchUnassigned(hostelId: number) {
        if (!hostelId) {
            setUnassigned([]);
            return;
        }
        setLoadingUnassigned(true);
        try {
            const data = await api.getWardenUnassignedHostellers(hostelId);
            setUnassigned(data || []);
        } catch (err) {
            console.error('Failed to load unassigned hostellers', err);
        } finally {
            setLoadingUnassigned(false);
        }
    }

    async function handleHostelChange(hostelId: number) {
        if (!hostelId || hostelId === selectedHostelId) return;
        setSelectedHostelId(hostelId);
        setPreview(null);
        setSelected(new Set());
        setLoading(true);
        try {
            await loadHostelScopedData(hostelId);
        } finally {
            setLoading(false);
        }
    }

    const departmentOptions = useMemo(() => {
        return Array.from(new Set(unassigned.map(u => u.student_department).filter(Boolean) as string[])).sort();
    }, [unassigned]);

    const degreeOptions = useMemo(() => {
        return Array.from(new Set(unassigned.map(u => u.student_degree).filter(Boolean) as string[])).sort();
    }, [unassigned]);

    const batchOptions = useMemo(() => {
        return Array.from(new Set(unassigned.map(u => u.student_batch).filter(Boolean) as string[])).sort();
    }, [unassigned]);

    const yearOptions = useMemo(() => {
        return Array.from(new Set(unassigned.map(u => u.student_study_year).filter(Boolean) as number[])).sort();
    }, [unassigned]);

    const filteredCount = useMemo(() => {
        return unassigned.filter(u => {
            if (filters.department && u.student_department !== filters.department) return false;
            if (filters.study_year && String(u.student_study_year) !== filters.study_year) return false;
            if (filters.degree && u.student_degree !== filters.degree) return false;
            if (filters.batch && u.student_batch !== filters.batch) return false;
            if (filters.gender && u.student_gender !== filters.gender) return false;
            return true;
        }).length;
    }, [unassigned, filters]);

    async function generateRecommendations() {
        if (!selectedHostelId) return;
        setGenerating(true);
        try {
            const params: any = {
                strategy: filters.strategy as 'fill' | 'spread',
            };
            if (filters.department) params.department = filters.department;
            if (filters.study_year) params.study_year = parseInt(filters.study_year, 10);
            if (filters.degree) params.degree = filters.degree;
            if (filters.batch) params.batch = filters.batch;
            if (filters.gender) params.gender = filters.gender;
            if (filters.limit) params.limit = parseInt(filters.limit, 10);

            const result: AutoAssignPreview = await api.previewAutoAssignHostelRooms(params, selectedHostelId);
            setPreview(result);
            setSelected(new Set(result.recommendations.map(r => r.student_id)));
        } catch (err: any) {
            alert(err.message || 'Failed to generate recommendations');
        } finally {
            setGenerating(false);
        }
    }

    async function confirmAssignments() {
        if (!preview || !selectedHostelId) return;
        const assignments = preview.recommendations
            .filter(rec => selected.has(rec.student_id))
            .map(rec => ({ student_id: rec.student_id, room_id: rec.room_id }));

        if (assignments.length === 0) {
            alert('Select at least one student to confirm.');
            return;
        }

        setConfirming(true);
        try {
            const result: AutoAssignResult = await api.confirmAutoAssignHostelRooms(assignments, selectedHostelId);
            setLastResult(result);
            setPreview(null);
            setSelected(new Set());
            await fetchUnassigned(selectedHostelId);
        } catch (err: any) {
            alert(err.message || 'Failed to confirm assignments');
        } finally {
            setConfirming(false);
        }
    }

    async function handleExport(format: 'excel' | 'pdf') {
        if (!selectedHostelId) return;
        setExporting(format);
        try {
            const params: any = {};
            if (filters.department) params.department = filters.department;
            if (filters.study_year) params.study_year = parseInt(filters.study_year, 10);
            if (filters.degree) params.degree = filters.degree;
            if (filters.batch) params.batch = filters.batch;
            if (filters.gender) params.gender = filters.gender;

            const blob = await api.downloadHostelAssignments(format, params, selectedHostelId);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            const date = new Date().toISOString().slice(0, 10);
            const hostelSlug = (hostel?.name || 'hostel').toLowerCase().replace(/\s+/g, '_');
            link.href = url;
            link.download = `${hostelSlug}_assignments_${date}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err: any) {
            alert(err.message || 'Failed to export assignments');
        } finally {
            setExporting(null);
        }
    }

    function toggleSelectAll(checked: boolean) {
        if (!preview) return;
        if (checked) {
            setSelected(new Set(preview.recommendations.map(r => r.student_id)));
        } else {
            setSelected(new Set());
        }
    }

    function toggleSelect(studentId: number) {
        setSelected(prev => {
            const next = new Set(prev);
            if (next.has(studentId)) next.delete(studentId);
            else next.add(studentId);
            return next;
        });
    }

    if (loading) {
        return (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-lg p-8 text-center">
                <Pulse size={32} className="text-slate-500 mx-auto mb-2 animate-pulse" />
                <p className="text-slate-500">Loading hostel...</p>
            </div>
        );
    }

    if (!hostel) {
        return (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-10 text-center">
                <Sparkle size={48} className="text-slate-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-300 mb-2">No Hostel Assignment</h3>
                <p className="text-slate-500 mb-4">You are not assigned to any active hostel.</p>
                <button
                    onClick={() => router.push('/admin/hostel')}
                    className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded-lg inline-flex items-center gap-2"
                >
                    <ArrowLeft size={16} />
                    Back to Dashboard
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                        <Sparkle size={28} weight="duotone" className="text-indigo-400" />
                        Hostel Auto Assign
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Generate recommendations, review, and confirm for the selected hostel.
                    </p>
                </div>
                <div className="flex items-end gap-3">
                    <div className="min-w-[260px]">
                        <label className="block text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-2">
                            Active Hostel ({hostels.length})
                        </label>
                        <select
                            value={selectedHostelId ?? ''}
                            onChange={(e) => void handleHostelChange(Number(e.target.value))}
                            className="w-full bg-slate-900/70 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                        >
                            {hostels.map((item) => (
                                <option key={item.id} value={item.id}>
                                    {item.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <button
                        onClick={() => router.push('/admin/hostel')}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg flex items-center gap-2"
                    >
                        <ArrowLeft size={16} />
                        Back to Dashboard
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="bg-slate-900/60 border border-slate-700/60 rounded-xl p-5">
                        <h2 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                            <Users size={16} />
                            Hostel Summary
                        </h2>
                        <div className="space-y-3 text-sm">
                            <div className="flex justify-between">
                                <span className="text-slate-500">Hostel</span>
                                <span className="text-slate-200">{hostel.name}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-500">Rooms</span>
                                <span className="text-slate-200 font-mono">{hostel.room_count}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-500">Occupancy</span>
                                <span className="text-slate-200 font-mono">{hostel.occupied_beds} / {hostel.capacity}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-500">Unassigned</span>
                                <span className="text-slate-200 font-mono">{unassigned.length}</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-900/60 border border-slate-700/60 rounded-xl p-5 lg:col-span-2">
                        <h2 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                            <Funnel size={16} />
                            Filters & Strategy
                        </h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                            <div>
                                <label className="block text-slate-500 mb-1">Department</label>
                                <select
                                    value={filters.department}
                                    onChange={(e) => setFilters({ ...filters, department: e.target.value })}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                    <option value="">All</option>
                                    {departmentOptions.map(dep => (
                                        <option key={dep} value={dep}>{dep}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-slate-500 mb-1">Study Year</label>
                                <select
                                    value={filters.study_year}
                                    onChange={(e) => setFilters({ ...filters, study_year: e.target.value })}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                    <option value="">All</option>
                                    {yearOptions.map(year => (
                                        <option key={year} value={year}>{year}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-slate-500 mb-1">Degree</label>
                                <select
                                    value={filters.degree}
                                    onChange={(e) => setFilters({ ...filters, degree: e.target.value })}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                    <option value="">All</option>
                                    {degreeOptions.map(deg => (
                                        <option key={deg} value={deg}>{deg}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-slate-500 mb-1">Batch</label>
                                <select
                                    value={filters.batch}
                                    onChange={(e) => setFilters({ ...filters, batch: e.target.value })}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                    <option value="">All</option>
                                    {batchOptions.map(batch => (
                                        <option key={batch} value={batch}>{batch}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-slate-500 mb-1">Gender</label>
                                <select
                                    value={filters.gender}
                                    onChange={(e) => setFilters({ ...filters, gender: e.target.value })}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                    <option value="">All</option>
                                    <option value="MALE">Male</option>
                                    <option value="FEMALE">Female</option>
                                    <option value="OTHER">Other</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-slate-500 mb-1">Limit</label>
                                <input
                                    type="number"
                                    min={1}
                                    value={filters.limit}
                                    onChange={(e) => setFilters({ ...filters, limit: e.target.value })}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                    placeholder="e.g., 25"
                                />
                            </div>
                            <div>
                                <label className="block text-slate-500 mb-1">Strategy</label>
                                <select
                                    value={filters.strategy}
                                    onChange={(e) => setFilters({ ...filters, strategy: e.target.value })}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                    <option value="fill">Fill Rooms</option>
                                    <option value="spread">Spread Rooms</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex items-center gap-3 mt-5">
                            <button
                                onClick={generateRecommendations}
                                disabled={generating}
                                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                            >
                                {generating ? (
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <Sparkle size={16} />
                                )}
                                Generate Recommendations
                            </button>
                            <button
                                onClick={() => setFilters({ department: '', study_year: '', degree: '', batch: '', gender: '', limit: '', strategy: 'fill' })}
                                className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded-lg"
                            >
                                Clear Filters
                            </button>
                            <button
                                onClick={() => handleExport('excel')}
                                disabled={exporting !== null}
                                className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                            >
                                {exporting === 'excel' ? (
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <CheckCircle size={16} />
                                )}
                                Export Excel
                            </button>
                            <button
                                onClick={() => handleExport('pdf')}
                                disabled={exporting !== null}
                                className="bg-amber-600 hover:bg-amber-500 disabled:opacity-60 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                            >
                                {exporting === 'pdf' ? (
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <CheckCircle size={16} />
                                )}
                                Export PDF
                            </button>
                            <span className="text-xs text-slate-500 ml-auto">
                                Filtered students: <strong className="text-slate-200">{filteredCount}</strong>
                            </span>
                        </div>
                    </div>
                </div>

            <div className="bg-slate-900/60 border border-slate-700/60 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-mono text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Sparkle size={16} />
                        Recommendations
                    </h2>
                    {preview && (
                        <div className="text-xs text-slate-500">
                            Recommended: {preview.recommended_count} • Skipped: {preview.skipped_count}
                        </div>
                    )}
                </div>

                {!preview ? (
                    <div className="text-slate-500 text-sm">Generate recommendations to see suggested assignments.</div>
                ) : preview.recommendations.length === 0 ? (
                    <div className="text-slate-500 text-sm">No recommendations found for the selected filters.</div>
                ) : (
                    <>
                        <div className="flex items-center gap-3 mb-3">
                            <label className="flex items-center gap-2 text-sm text-slate-400">
                                <input
                                    type="checkbox"
                                    checked={selected.size === preview.recommendations.length}
                                    onChange={(e) => toggleSelectAll(e.target.checked)}
                                />
                                Select all
                            </label>
                            <button
                                onClick={confirmAssignments}
                                disabled={confirming}
                                className="ml-auto bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm"
                            >
                                {confirming ? (
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <CheckCircle size={16} />
                                )}
                                Confirm Selected
                            </button>
                        </div>
                        <div className="overflow-x-auto border border-slate-800 rounded-lg">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-800/60 text-slate-400 uppercase text-xs">
                                    <tr>
                                        <th className="p-3">Select</th>
                                        <th className="p-3">Student</th>
                                        <th className="p-3">Reg No</th>
                                        <th className="p-3">Dept</th>
                                        <th className="p-3">Year</th>
                                        <th className="p-3">Degree</th>
                                        <th className="p-3">Batch</th>
                                        <th className="p-3">Gender</th>
                                        <th className="p-3">Room</th>
                                        <th className="p-3">Floor</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/60">
                                    {preview.recommendations.map((rec) => (
                                        <tr key={`${rec.student_id}-${rec.room_id}`} className="hover:bg-slate-800/40">
                                            <td className="p-3">
                                                <input
                                                    type="checkbox"
                                                    checked={selected.has(rec.student_id)}
                                                    onChange={() => toggleSelect(rec.student_id)}
                                                />
                                            </td>
                                            <td className="p-3 text-slate-200">{rec.student_name}</td>
                                            <td className="p-3 text-slate-400">{rec.student_register_number || '-'}</td>
                                            <td className="p-3 text-slate-400">{rec.department || '-'}</td>
                                            <td className="p-3 text-slate-400">{rec.study_year || '-'}</td>
                                            <td className="p-3 text-slate-400">{rec.degree || '-'}</td>
                                            <td className="p-3 text-slate-400">{rec.batch || '-'}</td>
                                            <td className="p-3 text-slate-400">{rec.gender || '-'}</td>
                                            <td className="p-3 text-slate-200 font-mono">{rec.room_number}</td>
                                            <td className="p-3 text-slate-400">{rec.room_floor ?? '-'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}
            </div>

            {lastResult && (
                <div className="bg-slate-900/60 border border-slate-700/60 rounded-xl p-5">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-sm font-mono text-slate-400 uppercase tracking-widest flex items-center gap-2">
                            <CheckCircle size={16} />
                            Last Assignment Result
                        </h2>
                        <div className="text-xs text-slate-500">
                            Assigned: {lastResult.assigned_count} • Skipped: {lastResult.skipped_count}
                        </div>
                    </div>
                    <div className="text-xs text-slate-500 mb-3">
                        {lastResult.created_by_name ? `Confirmed by ${lastResult.created_by_name}` : 'Confirmed by system'}
                        {lastResult.created_by_username ? ` (${lastResult.created_by_username})` : ''}
                        {lastResult.created_by_email ? ` • ${lastResult.created_by_email}` : ''}
                        {' • '}
                        {lastResult.created_at ? new Date(lastResult.created_at).toLocaleString() : 'Unknown time'}
                    </div>
                    {lastResult.assigned.length === 0 ? (
                        <div className="text-slate-500 text-sm">No assignments were made.</div>
                    ) : (
                        <div className="overflow-x-auto border border-slate-800 rounded-lg">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-800/60 text-slate-400 uppercase text-xs">
                                    <tr>
                                        <th className="p-3">Student</th>
                                        <th className="p-3">Reg No</th>
                                        <th className="p-3">Room</th>
                                        <th className="p-3">Floor</th>
                                        <th className="p-3">Assigned At</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/60">
                                    {lastResult.assigned.map((row) => (
                                        <tr key={`${row.student_id}-${row.room_number}`} className="hover:bg-slate-800/40">
                                            <td className="p-3 text-slate-200">{row.student_name}</td>
                                            <td className="p-3 text-slate-400">{row.student_register_number || '-'}</td>
                                            <td className="p-3 text-slate-200 font-mono">{row.room_number}</td>
                                            <td className="p-3 text-slate-400">{row.room_floor ?? '-'}</td>
                                            <td className="p-3 text-slate-500">{new Date(row.assigned_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            <div className="bg-slate-900/60 border border-slate-700/60 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-mono text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Users size={16} />
                        Unassigned Hostellers
                    </h2>
                    <button
                        onClick={() => selectedHostelId && fetchUnassigned(selectedHostelId)}
                        className="text-xs text-slate-400 hover:text-slate-200"
                    >
                        Refresh
                    </button>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                    Includes only hosteller students who were never assigned to any hostel room.
                </p>

                {loadingUnassigned ? (
                    <div className="text-slate-500 text-sm">Loading unassigned hostellers...</div>
                ) : unassigned.length === 0 ? (
                    <div className="text-slate-500 text-sm">No unassigned hostellers available.</div>
                ) : (
                    <div className="overflow-x-auto border border-slate-800 rounded-lg">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-800/60 text-slate-400 uppercase text-xs">
                                <tr>
                                    <th className="p-3">Student</th>
                                    <th className="p-3">Reg No</th>
                                    <th className="p-3">Email</th>
                                    <th className="p-3">Dept</th>
                                    <th className="p-3">Year</th>
                                    <th className="p-3">Degree</th>
                                    <th className="p-3">Batch</th>
                                    <th className="p-3">Gender</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/60">
                                {unassigned.map((student) => (
                                    <tr key={student.student_id} className="hover:bg-slate-800/40">
                                        <td className="p-3 text-slate-200">{student.student_name}</td>
                                        <td className="p-3 text-slate-400">{student.student_register_number || '-'}</td>
                                        <td className="p-3 text-slate-400">{student.student_email || '-'}</td>
                                        <td className="p-3 text-slate-400">{student.student_department || '-'}</td>
                                        <td className="p-3 text-slate-400">{student.student_study_year || '-'}</td>
                                        <td className="p-3 text-slate-400">{student.student_degree || '-'}</td>
                                        <td className="p-3 text-slate-400">{student.student_batch || '-'}</td>
                                        <td className="p-3 text-slate-400">{student.student_gender || '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
