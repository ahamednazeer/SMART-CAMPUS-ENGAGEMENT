'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import DocumentViewer from '@/components/DocumentViewer';
import DataTable from '@/components/DataTable';
import {
    Search,
    FileText,
    Download,
    Eye,
    Filter,
} from 'lucide-react';

export default function PilotDocumentsPage() {
    const [documents, setDocuments] = useState<any[]>([]);
    const [tags, setTags] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedTag, setSelectedTag] = useState<string | null>(null);

    // Viewer state
    const [isViewerOpen, setIsViewerOpen] = useState(false);
    const [viewerDoc, setViewerDoc] = useState<any>(null);
    const [viewerUrl, setViewerUrl] = useState<string>('');

    const fetchData = async () => {
        try {
            const [docsData, tagsData] = await Promise.all([
                api.getDocuments(),
                api.getDocumentTags()
            ]);
            setDocuments(docsData);
            setTags(tagsData);
        } catch (error) {
            console.error('Failed to fetch data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleDownload = async (doc: any) => {
        try {
            await api.downloadDocument(doc.id, doc.originalName);
        } catch (error) {
            console.error('Download failed:', error);
            alert('Failed to download document');
        }
    };

    const handleView = async (doc: any) => {
        try {
            const blobUrl = await api.getDocumentBlobUrl(doc.id);
            setViewerDoc(doc);
            setViewerUrl(blobUrl);
            setIsViewerOpen(true);
        } catch (error) {
            console.error('View failed:', error);
            alert('Failed to load document for preview');
        }
    };

    const closeViewer = () => {
        setIsViewerOpen(false);
        if (viewerUrl) {
            window.URL.revokeObjectURL(viewerUrl);
        }
        setViewerUrl('');
        setViewerDoc(null);
    };

    const filteredDocuments = documents.filter(doc => {
        const matchesSearch = doc.originalName.toLowerCase().includes(searchTerm.toLowerCase()) ||
            doc.description?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesTag = selectedTag ? doc.tags.includes(selectedTag) : true;
        return matchesSearch && matchesTag;
    });

    const columns = [
        {
            key: 'name',
            label: 'Document',
            render: (doc: any) => (
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-sm bg-slate-800 flex items-center justify-center text-blue-400">
                        <FileText className="w-5 h-5" />
                    </div>
                    <div>
                        <div className="font-medium text-slate-200">{doc.originalName}</div>
                        <div className="text-xs text-slate-500">{(doc.filesize / 1024 / 1024).toFixed(2)} MB</div>
                    </div>
                </div>
            )
        },
        {
            key: 'description',
            label: 'Description',
            render: (doc: any) => (
                <span className="text-sm text-slate-400 font-mono">
                    {doc.description || '-'}
                </span>
            )
        },
        {
            key: 'tags',
            label: 'Tags',
            render: (doc: any) => (
                <div className="flex flex-wrap gap-1">
                    {doc.tags.length > 0 ? doc.tags.map((tag: string) => (
                        <span key={tag} className="px-2 py-0.5 rounded-sm text-xs bg-slate-800 text-slate-400 border border-slate-700">
                            {tag}
                        </span>
                    )) : <span className="text-xs text-slate-500">-</span>}
                </div>
            )
        },
        {
            key: 'uploadedAt',
            label: 'Uploaded',
            render: (doc: any) => (
                <span className="text-sm text-slate-400 font-mono">
                    {new Date(doc.createdAt).toLocaleDateString()}
                </span>
            )
        },
        {
            key: 'actions',
            label: 'Actions',
            render: (doc: any) => (
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => handleView(doc)}
                        className="p-1.5 text-slate-400 hover:text-green-400 hover:bg-green-500/10 rounded-sm transition-colors"
                        title="View"
                    >
                        <Eye className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => handleDownload(doc)}
                        className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-sm transition-colors"
                        title="Download"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                </div>
            )
        }
    ];

    if (loading) return (
        <DashboardLayout userRole="PILOT" userName="Pilot" userEmail="pilot@airbase.mil">
            <div className="flex items-center justify-center h-64">
                <div className="text-slate-400 font-mono">Loading documents...</div>
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout userRole="PILOT" userName="Pilot" userEmail="pilot@airbase.mil">
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider text-slate-100">Documents</h1>
                    <p className="text-slate-400 mt-1 text-sm font-mono">Access manuals, SOPs, and training materials</p>
                </div>

                <div className="flex gap-4">
                    <div className="flex-1 flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm">
                        <Search className="w-5 h-5 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search documents..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="bg-transparent border-none focus:outline-none text-slate-200 w-full placeholder-slate-500 font-mono text-sm"
                        />
                    </div>
                    <div className="relative group">
                        <div className="flex items-center gap-2 px-4 py-4 bg-slate-800/40 border border-slate-700/60 rounded-sm cursor-pointer min-w-[200px]">
                            <Filter className="w-4 h-4 text-slate-500" />
                            <span className="text-slate-300 font-mono text-sm">{selectedTag || 'All Tags'}</span>
                        </div>
                        <div className="absolute top-full right-0 mt-2 w-full bg-slate-900 border border-slate-700 rounded-sm shadow-xl hidden group-hover:block z-10">
                            <div
                                className="px-4 py-2 hover:bg-slate-800 cursor-pointer text-slate-300 font-mono text-sm"
                                onClick={() => setSelectedTag(null)}
                            >
                                All Tags
                            </div>
                            {tags.map(tag => (
                                <div
                                    key={tag.id}
                                    className="px-4 py-2 hover:bg-slate-800 cursor-pointer text-slate-300 font-mono text-sm"
                                    onClick={() => setSelectedTag(tag.name)}
                                >
                                    {tag.displayName}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {filteredDocuments.length > 0 ? (
                    <DataTable
                        data={filteredDocuments}
                        columns={columns}
                        emptyMessage="No documents found."
                    />
                ) : (
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-12 text-center">
                        <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <p className="text-slate-400 font-mono">No documents available for your role</p>
                        <p className="text-xs text-slate-500 mt-2 font-mono">Contact your administrator if you need access to specific documents</p>
                    </div>
                )}
            </div>

            {/* Document Viewer Modal */}
            {viewerDoc && (
                <DocumentViewer
                    isOpen={isViewerOpen}
                    onClose={closeViewer}
                    documentUrl={viewerUrl}
                    documentName={viewerDoc.originalName}
                    mimeType={viewerDoc.mimetype}
                    onDownload={() => handleDownload(viewerDoc)}
                />
            )}
        </DashboardLayout>
    );
}
