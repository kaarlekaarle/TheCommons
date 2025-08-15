import React, { useState, useEffect } from 'react';
import { X, ExternalLink, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { listPolls } from '../lib/api';
import type { Poll, Label } from '../types';
import { flags } from '../config/flags';
import LabelChip from './ui/LabelChip';
import Button from './ui/Button';

interface LinkedPrinciplesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  label: Label;
  currentPollId: string;
}

export const LinkedPrinciplesDrawer: React.FC<LinkedPrinciplesDrawerProps> = ({
  isOpen,
  onClose,
  label,
  currentPollId
}) => {
  const [principles, setPrinciples] = useState<Poll[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchLinkedPrinciples = async () => {
    try {
      setLoading(true);
      setError(null);

      const linkedPolls = await listPolls({
        decision_type: 'level_a',
        label: label.slug,
        limit: 3
      });

      // Filter out the current poll if it's somehow included
      const filteredPolls = linkedPolls.filter(poll => poll.id !== currentPollId);
      setPrinciples(filteredPolls);
    } catch (err: unknown) {
      const error = err as { message?: string };
      setError(error?.message || 'Failed to load linked principles');
      console.error('Error fetching linked principles:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && flags.labelsEnabled) {
      fetchLinkedPrinciples();
    }
  }, [isOpen, label.slug, fetchLinkedPrinciples]);

  const handleExploreAll = () => {
    navigate(`/principles?label=${label.slug}`);
    onClose();
  };

  const handlePrincipleClick = (pollId: string) => {
    navigate(`/proposals/${pollId}`);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-xl transform transition-transform duration-300 ease-in-out">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <LabelChip label={label} size="sm" />
              <h2 className="text-lg font-semibold text-gray-900">
                Linked Principles
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Loading principles...</span>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-red-600 mb-4">{error}</p>
                <Button onClick={fetchLinkedPrinciples} variant="secondary">
                  Try Again
                </Button>
              </div>
            ) : principles.length === 0 ? (
              <div className="text-center py-8">
                <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No linked principles yet
                </h3>
                <p className="text-gray-600 mb-4">
                  This topic doesn't have any principles yet. Be the first to create one!
                </p>
                <Button onClick={handleExploreAll} variant="primary">
                  Create First Principle
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-gray-600 mb-4">
                  These principles guide decisions in <strong>{label.name}</strong>:
                </p>

                {principles.map((principle) => (
                  <div
                    key={principle.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors cursor-pointer"
                    onClick={() => handlePrincipleClick(principle.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">
                          {principle.title}
                        </h3>
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {principle.description}
                        </p>
                        {principle.direction_choice && (
                          <div className="mt-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {principle.direction_choice}
                            </span>
                          </div>
                        )}
                      </div>
                      <ExternalLink className="w-4 h-4 text-gray-400 ml-2 flex-shrink-0" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <Button
              onClick={handleExploreAll}
              variant="primary"
              className="w-full"
            >
              Explore All Principles in {label.name}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LinkedPrinciplesDrawer;
