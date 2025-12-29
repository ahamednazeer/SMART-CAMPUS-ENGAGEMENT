'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import DocumentViewer from '@/components/DocumentViewer';
import DataTable from '@/components/DataTable';
import { Search, FileText, Download, Eye, Filter } from 'lucide-react';

export default function TraineeDocumentsPage() {
    const [documents, setDocuments] = useState<any[]>([]);
    const [tags, setTags] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedTag, setSelectedTag] = useState<string | null>(null);
    const [isViewerOpen, setIsViewerOpen] = useState(false);
    const [viewerDoc, setViewerDoc] = useState<any>(null);
    const [viewerUrl, setViewerUrl] = useState<string>('');

    useEffect(() => {
        Promise.all([api.getDocuments(), api.getDocumentTags()]).then(([docs, t]) => { setDocuments(docs); setTags(t); }).finally(() => setLoading(false));
    }, []);

    const handleDownload = async (doc: any) => { await api.downloadDocument(doc.id, doc.originalName); };
    const handleView = async (doc: any) => { const url = await api.getDocumentBlobUrl(doc.id); setViewerDoc(doc); setViewerUrl(url); setIsViewerOpen(true); };
    const closeViewer = () => { setIsViewerOpen(false); if (viewerUrl) window.URL.revokeObjectURL(viewerUrl); setViewerUrl(''); setViewerDoc(null); };

    const filtered = documents.filter(d => (d.originalName.toLowerCase().includes(searchTerm.toLowerCase()) || d.description?.toLowerCase().includes(searchTerm.toLowerCase())) && (!selectedTag || d.tags.includes(selectedTag)));

    const columns = [
        { key: 'name', label: 'Document', render: (d: any) => (<div className="flex items-center gap-3"><div className="w-10 h-10 rounded-sm bg-slate-800 flex items-center justify-center text-blue-400"><FileText className="w-5 h-5" /></div><div><div className="font-medium text-slate-200">{d.originalName}</div><div className="text-xs text-slate-500">{(d.filesize / 1024 / 1024).toFixed(2)} MB</div></div></div>) },
        { key: 'description', label: 'Description', render: (d: any) => <span className="text-sm text-slate-400 font-mono">{d.description || '-'}</span> },
        { key: 'actions', label: 'Actions', render: (d: any) => (<div className="flex items-center gap-2"><button onClick={() => handleView(d)} className="p-1.5 text-slate-400 hover:text-green-400 hover:bg-green-500/10 rounded-sm"><Eye className="w-4 h-4" /></button><button onClick={() => handleDownload(d)} className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-sm"><Download className="w-4 h-4" /></button></div>) }
    ];

    if (loading) return <DashboardLayout userRole="TRAINEE" userName="Trainee" userEmail="trainee@airbase.mil"><div className="flex items-center justify-center h-64"><div className="text-slate-400 font-mono">Loading...</div></div></DashboardLayout>;

    return (
        <DashboardLayout userRole="TRAINEE" userName="Trainee" userEmail="trainee@airbase.mil">
            <div className="space-y-6">
                <div><h1 className="text-2xl font-chivo font-bold uppercase tracking-wider text-slate-100">Training Documents</h1><p className="text-slate-400 mt-1 text-sm font-mono">Training materials, study guides, and resources</p></div>
                <div className="flex gap-4">
                    <div className="flex-1 flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm"><Search className="w-5 h-5 text-slate-500" /><input type="text" placeholder="Search..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="bg-transparent border-none focus:outline-none text-slate-200 w-full placeholder-slate-500 font-mono text-sm" /></div>
                    <div className="relative group"><div className="flex items-center gap-2 px-4 py-4 bg-slate-800/40 border border-slate-700/60 rounded-sm cursor-pointer min-w-[180px]"><Filter className="w-4 h-4 text-slate-500" /><span className="text-slate-300 font-mono text-sm">{selectedTag || 'All Tags'}</span></div><div className="absolute top-full right-0 mt-2 w-full bg-slate-900 border border-slate-700 rounded-sm shadow-xl hidden group-hover:block z-10"><div className="px-4 py-2 hover:bg-slate-800 cursor-pointer text-slate-300 font-mono text-sm" onClick={() => setSelectedTag(null)}>All Tags</div>{tags.map(t => <div key={t.id} className="px-4 py-2 hover:bg-slate-800 cursor-pointer text-slate-300 font-mono text-sm" onClick={() => setSelectedTag(t.name)}>{t.displayName}</div>)}</div></div>
                </div>
                {filtered.length ? <DataTable data={filtered} columns={columns} emptyMessage="No documents." /> : <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-12 text-center"><FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" /><p className="text-slate-400 font-mono">No documents available</p></div>}
            </div>
            {viewerDoc && <DocumentViewer isOpen={isViewerOpen} onClose={closeViewer} documentUrl={viewerUrl} documentName={viewerDoc.originalName} mimeType={viewerDoc.mimetype} onDownload={() => handleDownload(viewerDoc)} />}
        </DashboardLayout>
    );
}
