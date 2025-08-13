import { useState, useEffect } from 'react';

interface ApiCall {
  id: string;
  method: string;
  url: string;
  status: number;
  timestamp: Date;
}

interface DebugOverlayProps {
  isVisible: boolean;
}

export default function DebugOverlay({ isVisible }: DebugOverlayProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [apiCalls, setApiCalls] = useState<ApiCall[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);

  // Listen for API calls
  useEffect(() => {
    const handleApiCall = (event: CustomEvent) => {
      const { method, url, status } = event.detail;
      const newCall: ApiCall = {
        id: Date.now().toString(),
        method,
        url,
        status,
        timestamp: new Date(),
      };
      
      setApiCalls(prev => {
        const updated = [newCall, ...prev.slice(0, 4)]; // Keep last 5
        return updated;
      });
    };

    window.addEventListener('api-call', handleApiCall as EventListener);
    return () => window.removeEventListener('api-call', handleApiCall as EventListener);
  }, []);

  // Listen for token changes
  useEffect(() => {
    const checkToken = () => {
      const storedToken = localStorage.getItem('token');
      setToken(storedToken);
    };

    checkToken();
    window.addEventListener('storage', checkToken);
    return () => window.removeEventListener('storage', checkToken);
  }, []);

  // Extract username from token (if available)
  useEffect(() => {
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUsername(payload.sub || payload.username || null);
      } catch {
        setUsername(null);
      }
    } else {
      setUsername(null);
    }
  }, [token]);

  if (!isVisible) return null;

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString();
  };

  const truncateToken = (token: string) => {
    if (token.length <= 10) return token;
    return `${token.slice(0, 5)}...${token.slice(-5)}`;
  };

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'text-green-500';
    if (status >= 400 && status < 500) return 'text-yellow-500';
    if (status >= 500) return 'text-red-500';
    return 'text-gray-500';
  };

  const clearLocalStorage = () => {
    localStorage.clear();
    window.location.reload();
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-gray-800 hover:bg-gray-700 text-white rounded-full w-8 h-8 flex items-center justify-center text-xs font-mono shadow-lg"
        title="Toggle Debug Overlay"
      >
        {isOpen ? '×' : 'D'}
      </button>

      {/* Debug Panel */}
      {isOpen && (
        <div className="absolute top-10 right-0 w-80 bg-gray-900 text-white rounded-lg shadow-xl border border-gray-700 max-h-96 overflow-hidden">
          <div className="p-3 border-b border-gray-700 bg-gray-800">
            <h3 className="text-sm font-semibold">Debug Overlay</h3>
          </div>
          
          <div className="p-3 space-y-3 max-h-80 overflow-y-auto">
            {/* Authentication Info */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide">Auth</h4>
              <div className="text-xs space-y-1">
                <div>
                  <span className="text-gray-400">Token: </span>
                  <span className="font-mono">
                    {token ? truncateToken(token) : 'None'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">User: </span>
                  <span className="font-mono">
                    {username || 'Unknown'}
                  </span>
                </div>
              </div>
            </div>

            {/* API Calls */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide">
                Recent API Calls ({apiCalls.length})
              </h4>
              <div className="space-y-1">
                {apiCalls.length === 0 ? (
                  <div className="text-xs text-gray-500 italic">No API calls yet</div>
                ) : (
                  apiCalls.map((call) => (
                    <div key={call.id} className="text-xs bg-gray-800 rounded p-2 space-y-1">
                      <div className="flex justify-between items-center">
                        <span className={`font-mono ${getStatusColor(call.status)}`}>
                          {call.method} {call.status}
                        </span>
                        <span className="text-gray-400 text-xs">
                          {formatTime(call.timestamp)}
                        </span>
                      </div>
                      <div className="text-gray-300 font-mono text-xs truncate" title={call.url}>
                        {call.url}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Cache Management */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide">Cache</h4>
              <button
                onClick={clearLocalStorage}
                className="w-full text-xs bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded"
                title="Clear localStorage and reload"
              >
                Clear Local Storage
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
