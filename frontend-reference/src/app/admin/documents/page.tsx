'use client';

import { useEffect, useState, useRef } from 'react';
import { api } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import DataTable from '@/components/DataTable';
import DocumentViewer from '@/components/DocumentViewer';
import {
    Upload,
    Search,
    FileText,
    Download,
    Trash2,
    Eye,
    Filter,
    X
} from 'lucide-react';

export default function DocumentManagementPage() {
    const [documents, setDocuments] = useState<any[]>([]);
    const [tags, setTags] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedTag, setSelectedTag] = useState<string | null>(null);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

    // Viewer state
    const [isViewerOpen, setIsViewerOpen] = useState(false);
    const [viewerDoc, setViewerDoc] = useState<any>(null);
    const [viewerUrl, setViewerUrl] = useState<string>('');

    // Upload state
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadForm, setUploadForm] = useState({
        description: '',
        tags: [] as string[],
        allowedRoles: [] as string[]
    });
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

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

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!uploadFile) return;

        setUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', uploadFile);
            formData.append('description', uploadForm.description);
            formData.append('tags', JSON.stringify(uploadForm.tags));
            formData.append('allowedRoles', JSON.stringify(uploadForm.allowedRoles));

            await api.uploadDocument(formData);
            await fetchData();
            setIsUploadModalOpen(false);
            setUploadFile(null);
            setUploadForm({ description: '', tags: [], allowedRoles: [] });
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Failed to upload document');
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this document?')) return;
        try {
            await api.deleteDocument(id);
            await fetchData();
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

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
                    <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-blue-400">
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
            key: 'tags',
            label: 'Tags',
            render: (doc: any) => (
                <div className="flex flex-wrap gap-1">
                    {doc.tags.map((tag: string) => (
                        <span key={tag} className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400 border border-slate-700">
                            {tag}
                        </span>
                    ))}
                </div>
            )
        },
        {
            key: 'roles',
            label: 'Access',
            render: (doc: any) => (
                <div className="flex flex-wrap gap-1">
                    {doc.allowedRoles.length === 0 ? (
                        <span className="text-xs text-slate-500">All Roles</span>
                    ) : (
                        doc.allowedRoles.map((role: string) => (
                            <span key={role} className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                {role}
                            </span>
                        ))
                    )}
                </div>
            )
        },
        {
            key: 'uploadedBy',
            label: 'Uploaded By',
            render: (doc: any) => (
                <div className="text-sm text-slate-400">
                    {doc.uploadedBy.firstName} {doc.uploadedBy.lastName}
                    <div className="text-xs text-slate-600">
                        {new Date(doc.createdAt).toLocaleDateString()}
                    </div>
                </div>
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
                    <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-sm transition-colors"
                        title="Delete"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            )
        }
    ];

    if (loading) return (
        <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
            <div className="text-slate-400">Loading documents...</div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider text-slate-100">Document Management</h1>
                        <p className="text-slate-400 mt-1 text-sm font-mono">Manage and organize system documentation</p>
                    </div>
                    <button
                        onClick={() => setIsUploadModalOpen(true)}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150"
                    >
                        <Upload className="w-4 h-4" />
                        Upload Document
                    </button>
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
                        {/* Simple dropdown for tags */}
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

                <DataTable
                    data={filteredDocuments}
                    columns={columns}
                    emptyMessage="No documents found."
                />

                {/* Upload Modal */}
                {isUploadModalOpen && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-modal">
                        <div className="bg-slate-900 border border-slate-700 rounded-sm w-full max-w-lg shadow-2xl">
                            <div className="flex items-center justify-between p-6 border-b border-slate-700">
                                <h2 className="text-xl font-chivo font-bold uppercase tracking-wider text-slate-100">Upload Document</h2>
                                <button onClick={() => setIsUploadModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <form onSubmit={handleUpload} className="p-6 space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs text-slate-500 uppercase tracking-wider font-mono">File</label>
                                    <div
                                        onClick={() => fileInputRef.current?.click()}
                                        className="border-2 border-dashed border-slate-700 rounded-sm p-8 text-center cursor-pointer hover:border-blue-500/50 transition-colors"
                                    >
                                        <input
                                            type="file"
                                            ref={fileInputRef}
                                            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                                            className="hidden"
                                        />
                                        {uploadFile ? (
                                            <div className="text-blue-400 font-medium flex items-center justify-center gap-2 font-mono">
                                                <FileText className="w-5 h-5" />
                                                {uploadFile.name}
                                            </div>
                                        ) : (
                                            <div className="text-slate-500">
                                                <Upload className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                                <p className="font-mono text-sm">Click to select a file</p>
                                                <p className="text-xs mt-1 font-mono">PDF, DOC, DOCX, TXT, MD (Max 10MB)</p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs text-slate-500 uppercase tracking-wider font-mono">Description</label>
                                    <input
                                        type="text"
                                        value={uploadForm.description}
                                        onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                                        className="w-full bg-slate-950 border border-slate-700 rounded-sm px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-sm"
                                        placeholder="Brief description of the document"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs text-slate-500 uppercase tracking-wider font-mono">Tags</label>
                                    <div className="flex flex-wrap gap-2">
                                        {tags.map(tag => (
                                            <button
                                                key={tag.id}
                                                type="button"
                                                onClick={() => {
                                                    const newTags = uploadForm.tags.includes(tag.name)
                                                        ? uploadForm.tags.filter(t => t !== tag.name)
                                                        : [...uploadForm.tags, tag.name];
                                                    setUploadForm({ ...uploadForm, tags: newTags });
                                                }}
                                                className={`px-3 py-1 rounded-sm text-xs font-mono font-medium border transition-colors ${uploadForm.tags.includes(tag.name)
                                                    ? 'bg-blue-950/50 text-blue-400 border-blue-500/50'
                                                    : 'bg-slate-950 text-slate-400 border-slate-700 hover:border-slate-600'
                                                    }`}
                                            >
                                                {tag.displayName}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs text-slate-500 uppercase tracking-wider font-mono">Allowed Roles</label>
                                    <div className="flex flex-wrap gap-2">
                                        {['PILOT', 'TECHNICIAN', 'COMMANDER', 'TRAINEE', 'EMERGENCY', 'FAMILY'].map(role => (
                                            <button
                                                key={role}
                                                type="button"
                                                onClick={() => {
                                                    const newRoles = uploadForm.allowedRoles.includes(role)
                                                        ? uploadForm.allowedRoles.filter(r => r !== role)
                                                        : [...uploadForm.allowedRoles, role];
                                                    setUploadForm({ ...uploadForm, allowedRoles: newRoles });
                                                }}
                                                className={`px-3 py-1 rounded-sm text-xs font-mono font-medium border transition-colors ${uploadForm.allowedRoles.includes(role)
                                                    ? 'bg-green-950/50 text-green-400 border-green-500/50'
                                                    : 'bg-slate-950 text-slate-400 border-slate-700 hover:border-slate-600'
                                                    }`}
                                            >
                                                {role}
                                            </button>
                                        ))}
                                    </div>
                                    <p className="text-xs text-slate-500 font-mono">Leave empty to allow all roles</p>
                                </div>

                                <div className="flex justify-end gap-3 pt-4 border-t border-slate-700 mt-6">
                                    <button
                                        type="button"
                                        onClick={() => setIsUploadModalOpen(false)}
                                        className="px-4 py-2.5 rounded-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors font-medium uppercase text-sm tracking-wide"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={uploading || !uploadFile}
                                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150 disabled:opacity-50"
                                    >
                                        {uploading ? (
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        ) : (
                                            <Upload className="w-4 h-4" />
                                        )}
                                        Upload
                                    </button>
                                </div>
                            </form>
                        </div>
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
