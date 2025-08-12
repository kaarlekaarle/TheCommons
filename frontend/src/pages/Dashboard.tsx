import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, User, Users } from 'lucide-react';
import { getMyDelegate, setDelegate, removeDelegate, searchUserByUsername } from '../lib/api';
import { useToast } from '../components/ui/useToast';
import type { DelegationInfo } from '../types';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import DebugRawData from '../components/ui/DebugRawData';


export default function Dashboard() {
  const [delegationInfo, setDelegationInfo] = useState<DelegationInfo | null>(null);
  const [searchUsername, setSearchUsername] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [settingDelegate, setSettingDelegate] = useState(false);
  const [removingDelegate, setRemovingDelegate] = useState(false);
  const [rawData, setRawData] = useState<any>(null);
  const { success, error: showError } = useToast();

  useEffect(() => {
    fetchDelegationInfo();
  }, []);

  const fetchDelegationInfo = async () => {
    try {
      const data = await getMyDelegate();
      setDelegationInfo(data);
      setRawData(data);
    } catch (err: unknown) {
      showError('Failed to load delegation info');
    }
  };

  const handleSearch = async () => {
    if (!searchUsername.trim()) return;
    
    try {
      setSearching(true);
      const results = await searchUserByUsername(searchUsername);
      const searchData = Array.isArray(results) ? results : [results];
      setSearchResults(searchData);
      setRawData({ delegationInfo, searchResults: searchData });
    } catch (err: unknown) {
      showError('Failed to search users');
    } finally {
      setSearching(false);
    }
  };

  const handleSetDelegate = async (userId: string) => {
    try {
      setSettingDelegate(true);
      await setDelegate(userId);
      await fetchDelegationInfo();
      success('Delegate set successfully');
      setSearchUsername('');
      setSearchResults([]);
    } catch (err: unknown) {
      const error = err as { message: string };
      showError(error.message || 'Failed to set delegate');
    } finally {
      setSettingDelegate(false);
    }
  };

  const handleRemoveDelegate = async () => {
    try {
      setRemovingDelegate(true);
      await removeDelegate();
      await fetchDelegationInfo();
      success('Delegate removed successfully');
    } catch (err: unknown) {
      const error = err as { message: string };
      showError(error.message || 'Failed to remove delegate');
    } finally {
      setRemovingDelegate(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link to="/proposals/new">
          <Button>
            <Plus className="w-4 h-4" />
            New Proposal
          </Button>
        </Link>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Quick Actions */}
        <div className="bg-surface border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-4">
            <Link to="/proposals/new">
              <Button className="w-full justify-start" variant="ghost">
                <Plus className="w-4 h-4 mr-3" />
                Create New Proposal
              </Button>
            </Link>
            <Link to="/proposals">
              <Button className="w-full justify-start" variant="ghost">
                <Users className="w-4 h-4 mr-3" />
                View All Proposals
              </Button>
            </Link>
            <Link to="/activity">
              <Button className="w-full justify-start" variant="ghost">
                <Users className="w-4 h-4 mr-3" />
                View Activity Feed
              </Button>
            </Link>
          </div>
        </div>

        {/* My Delegate */}
        <div className="bg-surface border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">My Delegate</h2>
          <div className="space-y-4">
            {delegationInfo?.has_delegate ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted">Current delegate:</span>
                  <Badge variant="success">{delegationInfo.delegate_username}</Badge>
                </div>
                <Button
                  onClick={handleRemoveDelegate}
                  loading={removingDelegate}
                  variant="ghost"
                  size="sm"
                  className="w-full"
                >
                  Remove Delegate
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-muted">
                  You don't have a delegate set. Set a delegate to automatically vote on your behalf when you don't vote on proposals.
                </p>
                
                {/* Search for delegate */}
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={searchUsername}
                      onChange={(e) => setSearchUsername(e.target.value)}
                      placeholder="Search for a user..."
                      className="flex-1 px-3 py-2 bg-bg border border-border rounded-md text-white placeholder-muted focus:ring-2 focus:ring-primary/50 focus:border-transparent"
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <Button
                      onClick={handleSearch}
                      loading={searching}
                      size="sm"
                    >
                      Search
                    </Button>
                  </div>
                  
                  {searchResults.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm text-muted">Search results:</p>
                      {searchResults.map((user) => (
                        <div
                          key={user.id}
                          className="flex items-center justify-between p-3 bg-bg rounded-md border border-border"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                              <User className="w-4 h-4 text-primary" />
                            </div>
                            <div>
                              <div className="font-medium">{user.username}</div>
                              <div className="text-xs text-muted">{user.email}</div>
                            </div>
                          </div>
                          <Button
                            onClick={() => handleSetDelegate(user.id)}
                            loading={settingDelegate}
                            size="sm"
                          >
                            Set as Delegate
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Welcome Message */}
      <div className="bg-surface border border-border rounded-lg p-6">
        <div className="text-center py-8">
          <div className="text-primary text-6xl mb-4">🏛️</div>
          <h2 className="text-2xl font-bold mb-2">Welcome to The Commons</h2>
          <p className="text-muted max-w-2xl mx-auto">
            The Commons is a democratic decision-making platform where you can create proposals, 
            vote on important matters, and delegate your voting power to trusted community members.
          </p>
        </div>
      </div>
      
      <DebugRawData data={rawData} title="Raw Dashboard Data" />
    </div>
  );
}
