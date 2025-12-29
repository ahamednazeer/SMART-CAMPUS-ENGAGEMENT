'use client';

import React, { useState, useRef, useEffect } from 'react';
import { X, PaperPlaneRight, Robot } from '@phosphor-icons/react';
import ReactMarkdown from 'react-markdown';
import { api } from '@/lib/api';

interface ChatBotProps {
    isOpen: boolean;
    onClose: () => void;
}

interface Message {
    role: 'user' | 'bot';
    content: string;
}

export default function ChatBot({ isOpen, onClose }: ChatBotProps) {
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async () => {
        if (!message.trim()) return;

        const userMessage: Message = { role: 'user', content: message };
        setMessages((prev) => [...prev, userMessage]);
        setMessage('');
        setLoading(true);

        try {
            const result = await api.sendChatMessage(message);

            const botMessage: Message = {
                role: 'bot',
                content: result.success
                    ? result.response || 'No response generated.'
                    : result.error || 'Failed to get response. Please try again.'
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error: any) {
            console.error('Failed to send message:', error);
            const errorMessage: Message = {
                role: 'bot',
                content: error.message || 'Connection error. Please check your network and try again.'
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div
            className="fixed bottom-4 right-4 w-[420px] h-[600px] bg-slate-900 border border-slate-700 rounded-lg shadow-2xl flex flex-col z-50"
            data-testid="chatbot-window"
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-gradient-to-r from-slate-800 to-slate-900">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center">
                        <Robot size={24} weight="duotone" className="text-blue-400" />
                    </div>
                    <div>
                        <span className="font-bold text-sm text-white">AeroOps AI</span>
                        <p className="text-xs text-slate-400">Role-Based Assistant</p>
                    </div>
                </div>
                <button
                    onClick={onClose}
                    className="text-slate-400 hover:text-white hover:bg-slate-700 p-2 rounded-lg transition-colors"
                    data-testid="close-chatbot-btn"
                >
                    <X size={20} />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-slate-500 text-sm mt-8">
                        <div className="w-16 h-16 rounded-full bg-blue-600/10 flex items-center justify-center mx-auto mb-4">
                            <Robot size={32} weight="duotone" className="text-blue-400/70" />
                        </div>
                        <p className="text-slate-300 font-medium">How can I help you today?</p>
                        <p className="text-slate-500 text-xs mt-1">Ask about your role-specific operations</p>
                        <div className="mt-6 grid gap-2">
                            <button
                                onClick={() => setMessage('Show my missions')}
                                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-2 rounded-lg border border-slate-700 transition-colors"
                            >
                                🛫 Show my missions
                            </button>
                            <button
                                onClick={() => setMessage('What is the weather status?')}
                                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-2 rounded-lg border border-slate-700 transition-colors"
                            >
                                🌤️ Weather status
                            </button>
                            <button
                                onClick={() => setMessage('Aircraft status')}
                                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-2 rounded-lg border border-slate-700 transition-colors"
                            >
                                ✈️ Aircraft status
                            </button>
                        </div>
                    </div>
                )}
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`${msg.role === 'user'
                            ? 'ml-8'
                            : 'mr-4'
                            }`}
                        data-testid={`message-${msg.role}`}
                    >
                        {msg.role === 'bot' && (
                            <div className="flex items-center gap-2 mb-2">
                                <div className="w-6 h-6 rounded-full bg-blue-600/20 flex items-center justify-center">
                                    <Robot size={14} className="text-blue-400" />
                                </div>
                                <span className="text-xs text-slate-500">AeroOps AI</span>
                            </div>
                        )}
                        <div className={`p-4 rounded-lg ${msg.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-800 border border-slate-700'
                            }`}
                        >
                            {msg.role === 'user' ? (
                                <p className="text-sm">{msg.content}</p>
                            ) : (
                                <div className="prose prose-invert prose-sm max-w-none
                                    prose-headings:text-blue-300 prose-headings:font-semibold prose-headings:mt-3 prose-headings:mb-2
                                    prose-h3:text-base prose-h4:text-sm
                                    prose-p:text-slate-300 prose-p:leading-relaxed prose-p:my-2
                                    prose-ul:my-2 prose-ul:space-y-1
                                    prose-li:text-slate-300 prose-li:my-0
                                    prose-strong:text-blue-300
                                    prose-code:text-emerald-400 prose-code:bg-slate-900 prose-code:px-1 prose-code:rounded
                                ">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="mr-4">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-6 h-6 rounded-full bg-blue-600/20 flex items-center justify-center">
                                <Robot size={14} className="text-blue-400" />
                            </div>
                            <span className="text-xs text-slate-500">AeroOps AI</span>
                        </div>
                        <div className="p-4 rounded-lg bg-slate-800 border border-slate-700">
                            <div className="flex items-center gap-2">
                                <div className="flex gap-1">
                                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                                </div>
                                <span className="text-sm text-slate-400">Thinking...</span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-slate-700 bg-slate-900">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                        placeholder="Ask about your operations..."
                        className="flex-1 bg-slate-800 border-slate-600 text-slate-100 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg placeholder:text-slate-500 text-sm px-4 py-3 border outline-none"
                        data-testid="chatbot-input"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={loading || !message.trim()}
                        className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-3 shadow-lg shadow-blue-600/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        data-testid="send-message-btn"
                    >
                        <PaperPlaneRight size={18} weight="fill" />
                    </button>
                </div>
            </div>
        </div>
    );
}
