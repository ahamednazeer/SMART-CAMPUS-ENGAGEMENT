'use client';

import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import mammoth from 'mammoth';
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Download, Loader2 } from 'lucide-react';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface DocumentViewerProps {
    isOpen: boolean;
    onClose: () => void;
    documentUrl: string;
    documentName: string;
    mimeType: string;
    onDownload: () => void;
}

export default function DocumentViewer({
    isOpen,
    onClose,
    documentUrl,
    documentName,
    mimeType,
    onDownload,
}: DocumentViewerProps) {
    const [numPages, setNumPages] = useState<number | null>(null);
    const [pageNumber, setPageNumber] = useState(1);
    const [scale, setScale] = useState(1.0);
    const [docxContent, setDocxContent] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const isPdf = mimeType === 'application/pdf';
    const isDocx = mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        mimeType === 'application/msword';
    const isText = mimeType === 'text/plain' || mimeType === 'text/markdown';

    useEffect(() => {
        if (!isOpen) return;

        setLoading(true);
        setError(null);
        setPageNumber(1);
        setDocxContent('');

        if (isDocx) {
            // Fetch and convert DOCX to HTML
            fetch(documentUrl)
                .then(response => response.arrayBuffer())
                .then(arrayBuffer => mammoth.convertToHtml({ arrayBuffer }))
                .then(result => {
                    setDocxContent(result.value);
                    setLoading(false);
                })
                .catch(err => {
                    console.error('Error loading DOCX:', err);
                    setError('Failed to load document');
                    setLoading(false);
                });
        } else if (isText) {
            // Fetch text content
            fetch(documentUrl)
                .then(response => response.text())
                .then(text => {
                    setDocxContent(`<pre style="white-space: pre-wrap; font-family: 'JetBrains Mono', monospace;">${text}</pre>`);
                    setLoading(false);
                })
                .catch(err => {
                    console.error('Error loading text:', err);
                    setError('Failed to load document');
                    setLoading(false);
                });
        } else if (isPdf) {
            setLoading(false);
        } else {
            setError('Unsupported file format for preview');
            setLoading(false);
        }
    }, [isOpen, documentUrl, isDocx, isPdf, isText]);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
        setLoading(false);
    }

    function onDocumentLoadError(err: Error) {
        console.error('PDF load error:', err);
        setError('Failed to load PDF');
        setLoading(false);
    }

    const goToPrevPage = () => setPageNumber(prev => Math.max(prev - 1, 1));
    const goToNextPage = () => setPageNumber(prev => Math.min(prev + 1, numPages || 1));
    const zoomIn = () => setScale(prev => Math.min(prev + 0.25, 3));
    const zoomOut = () => setScale(prev => Math.max(prev - 0.25, 0.5));

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-modal">
            <div className="bg-slate-900 border border-slate-700 rounded-sm w-full max-w-5xl h-[90vh] shadow-2xl flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700">
                    <div className="flex items-center gap-4">
                        <h2 className="text-lg font-chivo font-bold uppercase tracking-wider text-slate-100 truncate max-w-md">
                            {documentName}
                        </h2>
                        {isPdf && numPages && (
                            <span className="text-sm text-slate-400 font-mono">
                                Page {pageNumber} of {numPages}
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Zoom controls for PDF */}
                        {isPdf && (
                            <>
                                <button
                                    onClick={zoomOut}
                                    className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-sm transition-colors"
                                    title="Zoom Out"
                                >
                                    <ZoomOut className="w-4 h-4" />
                                </button>
                                <span className="text-xs text-slate-400 font-mono min-w-[50px] text-center">
                                    {Math.round(scale * 100)}%
                                </span>
                                <button
                                    onClick={zoomIn}
                                    className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-sm transition-colors"
                                    title="Zoom In"
                                >
                                    <ZoomIn className="w-4 h-4" />
                                </button>
                                <div className="w-px h-6 bg-slate-700 mx-2" />
                            </>
                        )}
                        <button
                            onClick={onDownload}
                            className="flex items-center gap-2 px-3 py-1.5 text-slate-300 hover:text-slate-100 hover:bg-slate-800 rounded-sm transition-colors text-sm font-mono"
                        >
                            <Download className="w-4 h-4" />
                            Download
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-sm transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto bg-slate-950 p-4">
                    {loading && (
                        <div className="flex items-center justify-center h-full">
                            <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                        </div>
                    )}

                    {error && (
                        <div className="flex flex-col items-center justify-center h-full text-slate-400">
                            <p className="text-lg font-mono mb-4">{error}</p>
                            <button
                                onClick={onDownload}
                                className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium uppercase text-sm tracking-wide transition-colors"
                            >
                                <Download className="w-4 h-4" />
                                Download Instead
                            </button>
                        </div>
                    )}

                    {!loading && !error && isPdf && (
                        <div className="flex justify-center">
                            <Document
                                file={documentUrl}
                                onLoadSuccess={onDocumentLoadSuccess}
                                onLoadError={onDocumentLoadError}
                                loading={
                                    <div className="flex items-center justify-center py-20">
                                        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                                    </div>
                                }
                            >
                                <Page
                                    pageNumber={pageNumber}
                                    scale={scale}
                                    renderTextLayer={false}
                                    renderAnnotationLayer={false}
                                    className="shadow-lg"
                                />
                            </Document>
                        </div>
                    )}

                    {!loading && !error && (isDocx || isText) && docxContent && (
                        <div
                            className="bg-white text-slate-900 rounded-sm p-8 max-w-4xl mx-auto prose prose-sm"
                            style={{ minHeight: '100%' }}
                            dangerouslySetInnerHTML={{ __html: docxContent }}
                        />
                    )}
                </div>

                {/* Footer with pagination for PDF */}
                {isPdf && numPages && numPages > 1 && (
                    <div className="flex items-center justify-center gap-4 p-4 border-t border-slate-700">
                        <button
                            onClick={goToPrevPage}
                            disabled={pageNumber <= 1}
                            className="flex items-center gap-1 px-3 py-1.5 text-slate-300 hover:text-slate-100 hover:bg-slate-800 rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-mono text-sm"
                        >
                            <ChevronLeft className="w-4 h-4" />
                            Previous
                        </button>
                        <span className="text-sm text-slate-400 font-mono">
                            {pageNumber} / {numPages}
                        </span>
                        <button
                            onClick={goToNextPage}
                            disabled={pageNumber >= numPages}
                            className="flex items-center gap-1 px-3 py-1.5 text-slate-300 hover:text-slate-100 hover:bg-slate-800 rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-mono text-sm"
                        >
                            Next
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
