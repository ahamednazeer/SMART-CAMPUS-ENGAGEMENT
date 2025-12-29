'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import DashboardLayout from '@/components/DashboardLayout';
import UserModal from '@/components/UserModal';
import { Plus, MagnifyingGlass, PencilSimple, Trash, Shield } from '@phosphor-icons/react';

export default function UserManagementPage() {
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<any>(null);

    const fetchUsers = async () => {
        try {
            const data = await api.getAllUsers();
            setUsers(data);
        } catch (error) {
            console.error('Failed to fetch users:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleCreateUser = async (userData: any) => {
        await api.createUser(userData);
        await fetchUsers();
    };

    const handleUpdateUser = async (userData: any) => {
        if (!selectedUser) return;
        await api.updateUser(selectedUser.id, userData);
        await fetchUsers();
    };

    const handleDeleteUser = async (id: string) => {
        if (!confirm('Are you sure you want to delete this user?')) return;
        try {
            await api.deleteUser(id);
            await fetchUsers();
        } catch (error) {
            console.error('Failed to delete user:', error);
        }
    };

    const filteredUsers = users.filter(user =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.lastName.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-400 font-mono">Loading users...</div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout userRole="ADMIN" userName="Admin" userEmail="admin@airbase.mil">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-chivo font-bold uppercase tracking-wider">User Management</h3>
                    <button
                        onClick={() => {
                            setSelectedUser(null);
                            setIsModalOpen(true);
                        }}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-2.5 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150"
                    >
                        <Plus size={16} weight="bold" />
                        Add User
                    </button>
                </div>

                <div className="flex items-center gap-4 bg-slate-800/40 border border-slate-700/60 p-4 rounded-sm">
                    <MagnifyingGlass className="text-slate-500" size={20} />
                    <input
                        type="text"
                        placeholder="Search users by name, email, or username..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-transparent border-none focus:outline-none text-slate-200 w-full placeholder-slate-500 font-mono text-sm"
                    />
                </div>

                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">User</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Email</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Role</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {filteredUsers.map((user) => (
                                    <tr key={user.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-sm bg-blue-950/50 border border-blue-800 flex items-center justify-center text-blue-400 font-bold text-xs font-mono">
                                                    {user.firstName[0]}{user.lastName[0]}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-slate-200">{user.firstName} {user.lastName}</div>
                                                    <div className="text-xs text-slate-500 font-mono">@{user.username}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-400 font-mono">{user.email}</td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider bg-blue-950/50 text-blue-400 border border-blue-800">
                                                <Shield size={12} weight="duotone" />
                                                {user.role}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <StatusBadge status={user.isActive ? 'ACTIVE' : 'INACTIVE'} />
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedUser(user);
                                                        setIsModalOpen(true);
                                                    }}
                                                    className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-950/50 rounded-sm transition-colors"
                                                >
                                                    <PencilSimple size={16} />
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteUser(user.id);
                                                    }}
                                                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-950/50 rounded-sm transition-colors"
                                                >
                                                    <Trash size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {filteredUsers.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center text-slate-500 font-mono">
                                            No users found matching your search.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                <UserModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSave={selectedUser ? handleUpdateUser : handleCreateUser}
                    user={selectedUser}
                />
            </div>
        </DashboardLayout>
    );
}
