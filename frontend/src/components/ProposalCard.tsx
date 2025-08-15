
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Calendar } from 'lucide-react';
import type { Poll } from '../types';
import LabelChip from './ui/LabelChip';
import { flags } from '../config/flags';
import { getProposalHref } from '../utils/navigation';

interface ProposalCardProps {
  poll: Poll;
  index?: number;
}

export default function ProposalCard({ poll, index = 0 }: ProposalCardProps) {
  const isLevelA = poll.decision_type === 'level_a';

  // Color schemes for different levels
  const levelAClasses = {
    card: "block card border-l-4 border-l-primary-500 relative overflow-hidden",
    header: "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary-500 to-primary-600"
  };

  const levelBClasses = {
    card: "block card border-l-4 border-l-success-500 relative overflow-hidden",
    header: "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-success-500 to-success-600"
  };

  const classes = isLevelA ? levelAClasses : levelBClasses;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
    >
      <Link
        to={getProposalHref(poll)}
        className={classes.card}
      >
        <div className={classes.header}></div>
        <div className="p-4">
          <div className="mb-3">
            <h3 className="text-2xl font-semibold text-strong line-clamp-2">
              {poll.title}
            </h3>
          </div>

          <p className="text-base text-body line-clamp-3 mb-4 leading-relaxed">
            {poll.description}
          </p>

          {/* Labels */}
          {flags.labelsEnabled && poll.labels && poll.labels.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {poll.labels.map((label, labelIndex) => (
                <LabelChip
                  key={`poll-${poll.id}-label-${label.id}-${labelIndex}`}
                  label={label}
                  size="sm"
                  onClick={(slug) => {
                    // Navigate to topic page
                    window.location.href = `/t/${slug}`;
                  }}
                />
              ))}
            </div>
          )}

          <div className="flex items-center text-sm text-subtle">
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
