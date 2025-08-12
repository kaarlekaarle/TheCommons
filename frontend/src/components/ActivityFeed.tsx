import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, RefreshCw } from 'lucide-react';
import { getActivityFeed } from '../lib/api';
import type { ActivityItem } from '../types';
import Button from './ui/Button';
import Empty from './ui/Empty';
import { useToast } from './ui/useToast';

export default function ActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
            <h1 className="text-2xl font-bold text-white">Activity</h1>
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
            <h1 className="text-2xl font-bold text-white">Activity</h1>
          </div>
          <Button onClick={fetchActivities} variant="ghost">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
        <div className="card-content">
          <div className="text-center py-12">
            <div className="text-muted text-6xl mb-4">📋</div>
            <h3 className="text-lg font-medium mb-2">Activity Feed Unavailable</h3>
            <p className="text-muted mb-4">The activity feed is currently being updated. Please check back later.</p>
            <Button onClick={fetchActivities} variant="ghost">
              Try Again
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
          <h1 className="text-2xl font-bold text-white">Activity</h1>
        </div>
        <Button onClick={fetchActivities} variant="ghost">
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {activities.length === 0 ? (
        <Empty
          icon={<Activity className="w-8 h-8" />}
          title="Nothing yet"
          subtitle="Activity will appear here as people propose, vote, and delegate."
        />
      ) : (
        <div className="space-y-4">
          <AnimatePresence>
            {activities.map((activity, index) => (
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
    </div>
  );
}
