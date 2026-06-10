import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { FileText, LogOut, Settings, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Sidebar() {
  const { user, token, logout } = useAuth();
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

      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Accessible Documents
        </h3>
        <div className="space-y-1">
          {documents.map(doc => (
            <div key={doc.id} className="flex items-center space-x-2 text-sm p-2 hover:bg-slate-800 rounded cursor-default">
              <FileText size={16} className="text-blue-400" />
              <span className="truncate flex-1">{doc.title}</span>
            </div>
          ))}
          {documents.length === 0 && (
            <p className="text-sm text-slate-500 italic">No documents available.</p>
          )}
        </div>
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
