import { useState, useEffect, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Activity, RefreshCw, Compass, Target } from 'lucide-react';
import { getActivityFeed } from '../lib/api';
import type { ActivityItem } from '../types';
import Button from './ui/Button';
import Empty from './ui/Empty';
import LabelChip from './ui/LabelChip';
import { useToast } from './ui/useToast';
import LevelFilter, { type LevelFilterType } from './LevelFilter';
import { flags } from '../config/flags';

export default function ActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<LevelFilterType>('all');
  const { error: showError } = useToast();

  const fetchActivities = useCallback(async () => {
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
  }, [showError]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  const handleLabelClick = (slug: string) => {
    window.location.href = `/t/${slug}?tab=all&page=1`;
  };

  // Memoize the filtered activities to prevent unnecessary re-renders
  const filteredActivities = useMemo(() => {
    const filtered = activities.filter(() => {
      if (activeFilter === 'all') return true;
      // For now, we'll show all activities since the API doesn't provide level info
      // In a real implementation, activities would have level information
      return true;
    });

    const levelAActivities = filtered.filter(item =>
      item.details.toLowerCase().includes('principle') ||
      item.details.toLowerCase().includes('level a')
    );
    const levelBActivities = filtered.filter(item =>
      item.details.toLowerCase().includes('action') ||
      item.details.toLowerCase().includes('level b')
    );
    const otherActivities = filtered.filter(item =>
      !levelAActivities.includes(item) && !levelBActivities.includes(item)
    );

    return { levelAActivities, levelBActivities, otherActivities, filtered };
  }, [activities, activeFilter]);

  const renderActivityItem = (activity: ActivityItem, index: number, cardClass: string, icon: React.ReactNode, iconColor: string) => (
    <motion.div
      key={activity.id}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: "easeOut", delay: index * 0.05 }}
      className={cardClass}
    >
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-8 h-8 ${iconColor} rounded-full flex items-center justify-center`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-white">{activity.user.username}</span>
            <span className="text-xs font-medium text-gray-300 capitalize bg-gray-700 px-2 py-0.5 rounded">{activity.type}</span>
          </div>
          <p className="text-sm text-gray-200 leading-relaxed">{activity.details}</p>

          {/* Labels */}
          {flags.labelsEnabled && activity.labels && activity.labels.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {activity.labels.map((label, labelIndex) => (
                <LabelChip
                  key={`activity-${activity.id}-label-${label.slug}-${labelIndex}`}
                  label={{
                    id: label.slug,
                    name: label.name,
                    slug: label.slug,
                    is_active: true,
                    created_at: '',
                    updated_at: ''
                  }}
                  size="sm"
                  onClick={handleLabelClick}
                />
              ))}
            </div>
          )}

          <time className="text-xs text-gray-400 mt-2 block">
            {new Date(activity.timestamp).toLocaleString()}
          </time>
        </div>
      </div>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-primary" />
            <h1 className="text-2xl font-bold text-strong">Community Activity</h1>
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
            <h1 className="text-2xl font-bold text-strong">Community Activity</h1>
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
          <h1 className="text-2xl font-bold text-strong">Community Activity</h1>
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
          {(() => {
            return (
              <>
                {/* Principle Activities */}
                {filteredActivities.levelAActivities.length > 0 && (activeFilter === 'all' || activeFilter === 'level_a') && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Compass className="w-5 h-5 text-blue-400" />
                      <h3 className="text-lg font-semibold text-blue-300">Principle Activities</h3>
                    </div>
                    {filteredActivities.levelAActivities.map((activity, index) => (
                      renderActivityItem(activity, index, "p-4 bg-gray-800 border border-gray-700 rounded-lg", <Compass className="w-4 h-4 text-blue-400" />, "bg-blue-500/20")
                    ))}
                  </div>
                )}

                {/* Action Activities */}
                {filteredActivities.levelBActivities.length > 0 && (activeFilter === 'all' || activeFilter === 'level_b') && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Target className="w-5 h-5 text-emerald-400" />
                      <h3 className="text-lg font-semibold text-emerald-300">Action Activities</h3>
                    </div>
                    {filteredActivities.levelBActivities.map((activity, index) => (
                      renderActivityItem(activity, index, "p-4 bg-gray-800 border border-gray-700 rounded-lg", <Target className="w-4 h-4 text-emerald-400" />, "bg-emerald-500/20")
                    ))}
                  </div>
                )}

                {/* Other Activities */}
                {filteredActivities.otherActivities.length > 0 && activeFilter === 'all' && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Activity className="w-5 h-5 text-blue-400" />
                      <h3 className="text-lg font-semibold text-blue-300">Other Activities</h3>
                    </div>
                    {filteredActivities.otherActivities.map((activity, index) => (
                      renderActivityItem(activity, index, "p-4 bg-gray-800 border border-gray-700 rounded-lg", <Activity className="w-4 h-4 text-blue-400" />, "bg-blue-500/20")
                    ))}
                  </div>
                )}

                {/* Empty state for filtered results */}
                {filteredActivities.filtered.length === 0 && activities.length > 0 && (
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
