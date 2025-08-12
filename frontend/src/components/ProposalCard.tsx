import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Calendar } from 'lucide-react';
import type { Poll } from '../types';

interface ProposalCardProps {
  poll: Poll;
  index?: number;
}

export default function ProposalCard({ poll, index = 0 }: ProposalCardProps) {
  const isLevelA = poll.decision_type === 'level_a';
  
  // Color schemes for different levels
  const levelAClasses = {
    card: "block bg-white border border-gov-border rounded-md shadow-gov hover:shadow-gov-md transition-all duration-200 border-l-4 border-l-gov-primary",
    directionLabel: "text-gov-primary font-bold text-xs"
  };
  
  const levelBClasses = {
    card: "block bg-white border border-gov-border rounded-md shadow-gov hover:shadow-gov-md transition-all duration-200 border-l-4 border-l-gov-secondary",
    directionLabel: "text-gov-secondary font-bold text-xs"
  };
  
  const classes = isLevelA ? levelAClasses : levelBClasses;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
    >
      <Link
        to={`/proposals/${poll.id}`}
        className={classes.card}
      >
        <div className="p-4">
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-gov-text line-clamp-2">
              {poll.title}
            </h3>
          </div>
          
          <p className="text-sm text-gov-text-muted line-clamp-3 mb-4 leading-relaxed">
            {poll.description}
          </p>
          
          {isLevelA && poll.direction_choice && (
            <div className="mb-4">
              <p className={classes.directionLabel}>
                {poll.direction_choice}
              </p>
            </div>
          )}
          
          <div className="flex items-center text-xs text-gov-text-muted">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(poll.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
