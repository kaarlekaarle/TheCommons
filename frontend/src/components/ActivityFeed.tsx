import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, RefreshCw, Compass, Target } from 'lucide-react';
import { getActivityFeed } from '../lib/api';
import type { ActivityItem } from '../types';
import Button from './ui/Button';
import Empty from './ui/Empty';
import { useToast } from './ui/useToast';
import LevelFilter, { type LevelFilterType } from './LevelFilter';

export default function ActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<LevelFilterType>('all');
  const { error: showError } = useToast();

  const fetchActivities = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getActivityFeed();
      setActivities(data);
    } catch (err: unknown) {
      const error = err as { message: string; status?: number; response?: { status?: number } };
      console.log('Activity feed error:', error);
      
      // Handle different error response structures
      const status = error.status || error.response?.status;
      if (status === 404) {
        setError('Activity feed is currently unavailable');
      } else {
        setError(error.message || 'Failed to load activity feed');
        showError('Failed to load activity feed');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-primary" />
            <h1 className="text-2xl font-bold text-white">Community Activity</h1>
          </div>
          <Button variant="ghost" disabled>
            <RefreshCw className="w-4 h-4 animate-spin" />
          </Button>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-primary" />
            <h1 className="text-2xl font-bold text-white">Community Activity</h1>
          </div>
          <Button onClick={fetchActivities} variant="ghost">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
        <div className="card-content">
          <div className="text-center py-12">
            <div className="text-muted text-6xl mb-4">📋</div>
            <h3 className="text-lg font-medium mb-2">Activity Feed Unavailable</h3>
            <p className="text-muted mb-4">Try again later.</p>
            <Button onClick={fetchActivities} variant="ghost">
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold text-white">Community Activity</h1>
        </div>
        <Button onClick={fetchActivities} variant="ghost">
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Level Filter */}
      <div className="mb-8">
        <LevelFilter 
          activeFilter={activeFilter} 
          onFilterChange={setActiveFilter}
          className="mb-6"
        />
      </div>

      {activities.length === 0 ? (
        <Empty
          icon={<Activity className="w-8 h-8" />}
          title="Nothing yet"
          subtitle="When proposals, votes, or delegations happen, they'll appear here."
        />
      ) : (
        <div className="space-y-6">
          {/* Filter activities by level */}
          {(() => {
            const filteredActivities = activities.filter(activity => {
              if (activeFilter === 'all') return true;
              // For now, we'll show all activities since the API doesn't provide level info
              // In a real implementation, activities would have level information
              return true;
            });

            const levelAActivities = filteredActivities.filter(activity => 
              activity.details.toLowerCase().includes('principle') || 
              activity.details.toLowerCase().includes('level a')
            );
            const levelBActivities = filteredActivities.filter(activity => 
              activity.details.toLowerCase().includes('action') || 
              activity.details.toLowerCase().includes('level b')
            );
            const otherActivities = filteredActivities.filter(activity => 
              !levelAActivities.includes(activity) && !levelBActivities.includes(activity)
            );

            return (
              <>
                {/* Level A Activities */}
                {levelAActivities.length > 0 && (activeFilter === 'all' || activeFilter === 'level_a') && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Compass className="w-5 h-5 text-blue-300" />
                      <h3 className="text-lg font-semibold text-blue-200">Principle Activities</h3>
                    </div>
                    <AnimatePresence>
                      {levelAActivities.map((activity, index) => (
                        <motion.div
                          key={activity.id}
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.18, ease: "easeOut", delay: index * 0.05 }}
                          className="p-4 card-level-a"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center">
                              <Compass className="w-4 h-4 text-blue-300" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-white">{activity.user.username}</span>
                                <span className="text-xs text-blue-300 capitalize">{activity.type}</span>
                              </div>
                              <p className="text-sm text-muted">{activity.details}</p>
                              <time className="text-xs text-muted mt-2 block">
                                {new Date(activity.timestamp).toLocaleString()}
                              </time>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                )}

                {/* Level B Activities */}
                {levelBActivities.length > 0 && (activeFilter === 'all' || activeFilter === 'level_b') && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Target className="w-5 h-5 text-emerald-300" />
                      <h3 className="text-lg font-semibold text-emerald-200">Action Activities</h3>
                    </div>
                    <AnimatePresence>
                      {levelBActivities.map((activity, index) => (
                        <motion.div
                          key={activity.id}
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.18, ease: "easeOut", delay: index * 0.05 }}
                          className="p-4 card-level-b"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-emerald-500/20 rounded-full flex items-center justify-center">
                              <Target className="w-4 h-4 text-emerald-300" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-white">{activity.user.username}</span>
                                <span className="text-xs text-emerald-300 capitalize">{activity.type}</span>
                              </div>
                              <p className="text-sm text-muted">{activity.details}</p>
                              <time className="text-xs text-muted mt-2 block">
                                {new Date(activity.timestamp).toLocaleString()}
                              </time>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                )}

                {/* Other Activities */}
                {otherActivities.length > 0 && activeFilter === 'all' && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Activity className="w-5 h-5 text-primary" />
                      <h3 className="text-lg font-semibold text-white">Other Activities</h3>
                    </div>
                    <AnimatePresence>
                      {otherActivities.map((activity, index) => (
                        <motion.div
                          key={activity.id}
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.18, ease: "easeOut", delay: index * 0.05 }}
                          className="p-4 bg-surface border border-border rounded-lg"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                              <Activity className="w-4 h-4 text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-white">{activity.user.username}</span>
                                <span className="text-xs text-muted capitalize">{activity.type}</span>
                              </div>
                              <p className="text-sm text-muted">{activity.details}</p>
                              <time className="text-xs text-muted mt-2 block">
                                {new Date(activity.timestamp).toLocaleString()}
                              </time>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                )}

                {/* Empty state for filtered results */}
                {filteredActivities.length === 0 && activities.length > 0 && (
                  <div className="text-center py-12">
                    <p className="text-muted mb-4">
                      No {activeFilter === 'level_a' ? 'principle' : 'action'} activities found.
                    </p>
                    <Button onClick={() => setActiveFilter('all')}>
                      Show All Activities
                    </Button>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
}
