'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import {
    ArrowLeft, Hash, Pin, Send, Users, Volume2, Search,
    MoreVertical, Reply, Trash2, MessageCircle, Plus
} from 'lucide-react';
import Link from 'next/link';

interface Circle {
    id: number;
    name: string;
    description?: string;
    subject_code?: string;
    has_voice_room: boolean;
    voice_room_url?: string;
}

interface Channel {
    id: number;
    circle_id: number;
    name: string;
    description?: string;
    channel_type: string;
    is_readonly: boolean;
}

interface Message {
    id: number;
    channel_id: number;
    user_id: number;
    content: string;
    parent_id?: number;
    thread_count: number;
    is_pinned: boolean;
    created_at: string;
}

export default function StudyCirclesPage() {
    const [circles, setCircles] = useState<Circle[]>([]);
    const [selectedCircle, setSelectedCircle] = useState<Circle | null>(null);
    const [channels, setChannels] = useState<Channel[]>([]);
    const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loadCircles();
    }, []);

    useEffect(() => {
        if (selectedCircle) {
            loadChannels(selectedCircle.id);
        }
    }, [selectedCircle]);

    useEffect(() => {
        if (selectedChannel) {
            loadMessages(selectedChannel.id);
        }
    }, [selectedChannel]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadCircles = async () => {
        try {
            setLoading(true);
            const data = await api.getMyStudyCircles();
            setCircles(data);
            if (data.length > 0 && !selectedCircle) {
                setSelectedCircle(data[0]);
            }
        } catch (error) {
            console.error('Error loading circles:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadChannels = async (circleId: number) => {
        try {
            const data = await api.getCircleChannels(circleId);
            setChannels(data);
            if (data.length > 0) {
                setSelectedChannel(data[0]);
            }
        } catch (error) {
            console.error('Error loading channels:', error);
        }
    };

    const loadMessages = async (channelId: number) => {
        try {
            const circle = selectedCircle;
            if (!circle) return;
            const data = await api.getChannelMessages(circle.id, channelId);
            setMessages(data.reverse());
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim() || !selectedCircle || !selectedChannel) return;

        try {
            await api.postMessage(selectedCircle.id, selectedChannel.id, newMessage);
            setNewMessage('');
            loadMessages(selectedChannel.id);
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    const formatTime = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const today = new Date();
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        }
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
            </div>
        );
    }

    if (circles.length === 0) {
        return (
            <div className="p-6">
                <Link href="/dashboard/student/learning" className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6">
                    <ArrowLeft className="w-5 h-5" />
                    Back to Learning Hub
                </Link>
                <div className="text-center py-16 bg-gray-50 dark:bg-gray-800 rounded-xl">
                    <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Study Circles</h2>
                    <p className="text-gray-500 dark:text-gray-400 mb-6">Join study circles to collaborate with peers</p>
                    <button
                        onClick={() => api.autoEnrollCircles().then(loadCircles)}
                        className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                        Auto-Join Based on Courses
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-[calc(100vh-100px)] flex">
            {/* Sidebar - Circles & Channels */}
            <div className="w-64 bg-gray-900 text-white flex flex-col">
                {/* Circle Selector */}
                <div className="p-3 border-b border-gray-700">
                    <select
                        value={selectedCircle?.id || ''}
                        onChange={(e) => {
                            const circle = circles.find(c => c.id === parseInt(e.target.value));
                            setSelectedCircle(circle || null);
                        }}
                        className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 border border-gray-700 focus:ring-2 focus:ring-purple-500"
                    >
                        {circles.map(circle => (
                            <option key={circle.id} value={circle.id}>{circle.name}</option>
                        ))}
                    </select>
                </div>

                {/* Channels */}
                <div className="flex-1 overflow-y-auto p-3">
                    <div className="text-xs uppercase text-gray-400 font-semibold mb-2">Text Channels</div>
                    {channels.filter(c => c.channel_type !== 'VOICE').map(channel => (
                        <button
                            key={channel.id}
                            onClick={() => setSelectedChannel(channel)}
                            className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md mb-1 transition-colors ${selectedChannel?.id === channel.id
                                    ? 'bg-gray-700 text-white'
                                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                                }`}
                        >
                            <Hash className="w-4 h-4 flex-shrink-0" />
                            <span className="truncate">{channel.name}</span>
                            {channel.is_readonly && (
                                <span className="text-xs bg-gray-600 px-1 rounded ml-auto">RO</span>
                            )}
                        </button>
                    ))}

                    {selectedCircle?.has_voice_room && (
                        <>
                            <div className="text-xs uppercase text-gray-400 font-semibold mt-4 mb-2">Voice Room</div>
                            <button
                                onClick={() => window.open(selectedCircle.voice_room_url, '_blank')}
                                className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
                            >
                                <Volume2 className="w-4 h-4" />
                                <span>Voice Chat</span>
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col bg-white dark:bg-gray-800">
                {/* Channel Header */}
                <div className="h-14 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                        <Hash className="w-5 h-5 text-gray-500" />
                        <span className="font-semibold text-gray-900 dark:text-white">
                            {selectedChannel?.name || 'Select a channel'}
                        </span>
                        {selectedChannel?.description && (
                            <span className="text-sm text-gray-500 hidden md:block">— {selectedChannel.description}</span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 pr-4 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-md text-sm focus:ring-2 focus:ring-purple-500 border-none"
                            />
                        </div>
                        <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md">
                            <Users className="w-5 h-5 text-gray-500" />
                        </button>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 ? (
                        <div className="text-center py-12">
                            <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                            <p className="text-gray-500">No messages yet. Start the conversation!</p>
                        </div>
                    ) : (
                        messages.map((message, idx) => {
                            const showDate = idx === 0 ||
                                formatDate(message.created_at) !== formatDate(messages[idx - 1].created_at);

                            return (
                                <React.Fragment key={message.id}>
                                    {showDate && (
                                        <div className="flex items-center gap-4 my-4">
                                            <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
                                            <span className="text-xs font-medium text-gray-500">{formatDate(message.created_at)}</span>
                                            <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
                                        </div>
                                    )}
                                    <div className="group flex gap-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 -mx-4 px-4 py-2 rounded-md">
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white font-semibold flex-shrink-0">
                                            U{message.user_id % 10}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-baseline gap-2">
                                                <span className="font-semibold text-gray-900 dark:text-white">User {message.user_id}</span>
                                                <span className="text-xs text-gray-500">{formatTime(message.created_at)}</span>
                                                {message.is_pinned && (
                                                    <Pin className="w-3 h-3 text-amber-500" />
                                                )}
                                            </div>
                                            <p className="text-gray-700 dark:text-gray-300 break-words">{message.content}</p>
                                            {message.thread_count > 0 && (
                                                <button className="mt-1 text-sm text-purple-600 hover:underline flex items-center gap-1">
                                                    <Reply className="w-3 h-3" />
                                                    {message.thread_count} replies
                                                </button>
                                            )}
                                        </div>
                                        <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1">
                                            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded">
                                                <Reply className="w-4 h-4 text-gray-500" />
                                            </button>
                                            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded">
                                                <Pin className="w-4 h-4 text-gray-500" />
                                            </button>
                                        </div>
                                    </div>
                                </React.Fragment>
                            );
                        })
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Message Input */}
                {selectedChannel && !selectedChannel.is_readonly && (
                    <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200 dark:border-gray-700">
                        <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-2">
                            <button type="button" className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded">
                                <Plus className="w-5 h-5 text-gray-500" />
                            </button>
                            <input
                                type="text"
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                placeholder={`Message #${selectedChannel?.name}`}
                                className="flex-1 bg-transparent border-none focus:ring-0 text-gray-900 dark:text-white placeholder-gray-500"
                            />
                            <button
                                type="submit"
                                disabled={!newMessage.trim()}
                                className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
