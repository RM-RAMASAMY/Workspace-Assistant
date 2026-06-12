import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import { apiCall } from '../utils/api';
import { FileText, LogOut, Settings, MessageSquare, Plus, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Sidebar({
  onOpenDocument,
  activeDocumentId,
  onOpenChat,
  onNewChat,
  activeSessionId,
}) {
  const { user, token, logout } = useAuth();
  const { sessions, deleteChat } = useChat();
  const [documents, setDocuments] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      apiCall('/documents/', 'GET', null, token)
        .then(setDocuments)
        .catch(console.error);
    }
  }, [token]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sortedSessions = [...sessions].sort(
    (a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)
  );

  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen text-slate-300">
      <div className="p-4 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
          {user?.name?.charAt(0) || 'U'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{user?.name}</p>
          <p className="text-xs text-slate-400 truncate capitalize">{user?.role_id === 1 ? 'Admin' : 'Employee'}</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Chat History
            </h3>
            <button
              type="button"
              onClick={onNewChat}
              className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              title="New chat"
            >
              <Plus size={16} />
            </button>
          </div>
          <div className="space-y-1">
            {sortedSessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center gap-1 rounded ${
                  activeSessionId === session.id
                    ? 'bg-blue-600/20 border border-blue-500/30'
                    : 'hover:bg-slate-800'
                }`}
              >
                <button
                  type="button"
                  onClick={() => onOpenChat(session.id)}
                  className="flex min-w-0 flex-1 items-center space-x-2 p-2 text-left text-sm"
                >
                  <MessageSquare size={16} className="text-blue-400 shrink-0" />
                  <span className="truncate">{session.title}</span>
                </button>
                <button
                  type="button"
                  onClick={() => deleteChat(session.id)}
                  className="mr-1 rounded p-1 text-slate-500 opacity-0 hover:bg-slate-700 hover:text-red-300 group-hover:opacity-100"
                  title="Delete chat"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Accessible Documents
          </h3>
          <div className="space-y-1">
            {documents.map((doc) => (
              <button
                key={doc.id}
                type="button"
                onClick={() => onOpenDocument({ id: doc.id, title: doc.title })}
                className={`flex w-full items-center space-x-2 text-sm p-2 rounded text-left transition-colors ${
                  activeDocumentId === doc.id
                    ? 'bg-blue-600/20 text-blue-200 border border-blue-500/30'
                    : 'hover:bg-slate-800'
                }`}
              >
                <FileText size={16} className="text-blue-400 shrink-0" />
                <span className="truncate flex-1">{doc.title}</span>
              </button>
            ))}
            {documents.length === 0 && (
              <p className="text-sm text-slate-500 italic">No documents available.</p>
            )}
          </div>
        </section>
      </div>

      <div className="p-4 border-t border-slate-800 space-y-2">
        {user?.access_level === 4 && (
          <button className="flex items-center space-x-2 text-sm p-2 w-full hover:bg-slate-800 rounded text-left transition-colors">
            <Settings size={16} />
            <span>Admin Panel</span>
          </button>
        )}
        <button onClick={handleLogout} className="flex items-center space-x-2 text-sm p-2 w-full hover:bg-slate-800 text-red-400 rounded text-left transition-colors">
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
