import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Users, 
  Vote, 
  MessageCircle, 
  TrendingUp, 
  Shield, 
  Globe,
  ArrowRight,
  Calendar,
  User,
  BarChart3
} from 'lucide-react';
import { listPolls } from '../lib/api';
import type { Poll } from '../types';
import Button from '../components/ui/Button';
import { useToast } from '../components/ui/useToast';

export default function Dashboard() {
  const [recentPolls, setRecentPolls] = useState<Poll[]>([]);
  const [loading, setLoading] = useState(true);
  const { error: showError } = useToast();

  useEffect(() => {
    fetchRecentPolls();
  }, []);

  const fetchRecentPolls = async () => {
    try {
      setLoading(true);
      const polls = await listPolls();
      // Get the 6 most recent polls
      const recent = polls.slice(0, 6);
      setRecentPolls(recent);
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to load recent polls:', error.message);
      showError('Failed to load recent proposals');
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: <Vote className="w-6 h-6" />,
      title: "Democratic Voting",
      description: "Participate in community decisions with transparent voting mechanisms"
    },
    {
      icon: <MessageCircle className="w-6 h-6" />,
      title: "Community Discussion",
      description: "Engage in meaningful conversations with reaction-based comments"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Delegation System",
      description: "Delegate your vote to trusted community members"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Real-time Results",
      description: "See live voting results and community engagement metrics"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Secure & Transparent",
      description: "Built with security and transparency as core principles"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Community Focused",
      description: "Designed to strengthen local communities and democratic participation"
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-white mb-4">
          Welcome to The Commons
        </h1>
        <p className="text-xl text-muted max-w-3xl mx-auto leading-relaxed">
          A democratic platform for community decision-making, designed to empower local communities 
          through transparent voting, meaningful discussions, and collective action.
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Left Column - About & Features */}
        <div className="space-y-8">
          {/* About Section */}
          <section className="p-6 bg-surface border border-border rounded-lg">
            <h2 className="text-2xl font-semibold text-white mb-4">About The Commons</h2>
            <div className="space-y-4 text-muted">
              <p>
                The Commons is a digital platform that reimagines how communities make decisions together. 
                We believe that strong communities are built on active participation, transparent processes, 
                and inclusive dialogue.
              </p>
              <p>
                Our platform combines modern democratic principles with intuitive technology, making it easy 
                for community members to propose ideas, discuss options, and vote on important decisions 
                that affect their shared future.
              </p>
              <p>
                Whether you're part of a neighborhood association, a local organization, or any community 
                group, The Commons provides the tools you need to make collective decisions more effectively 
                and inclusively.
              </p>
            </div>
          </section>

          {/* Features Grid */}
          <section>
            <h2 className="text-2xl font-semibold text-white mb-6">Current Features</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 bg-surface border border-border rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    <div className="text-primary flex-shrink-0 mt-1">
                      {feature.icon}
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-1">{feature.title}</h3>
                      <p className="text-sm text-muted">{feature.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </section>

          {/* Quick Actions */}
          <section className="p-6 bg-surface border border-border rounded-lg">
            <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link to="/proposals/new">
                <Button className="w-full justify-start" variant="primary">
                  <Vote className="w-4 h-4 mr-2" />
                  Create New Proposal
                </Button>
              </Link>
              <Link to="/proposals">
                <Button className="w-full justify-start" variant="ghost">
                  <BarChart3 className="w-4 h-4 mr-2" />
                  View All Proposals
                </Button>
              </Link>
              <Link to="/activity">
                <Button className="w-full justify-start" variant="ghost">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Recent Activity
                </Button>
              </Link>
            </div>
          </section>
        </div>

        {/* Right Column - Recent Proposals */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-white">Recent Proposals</h2>
            <Link to="/proposals">
              <Button variant="ghost" size="sm">
                View All
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>

          {loading ? (
            <div className="space-y-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="p-4 bg-surface border border-border rounded-lg animate-pulse">
                  <div className="h-4 bg-border rounded mb-2"></div>
                  <div className="h-3 bg-border rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : recentPolls.length > 0 ? (
            <div className="space-y-4">
              {recentPolls.map((poll) => (
                <motion.div
                  key={poll.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-4 bg-surface border border-border rounded-lg hover:border-primary/50 transition-colors"
                >
                  <Link to={`/proposals/${poll.id}`}>
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="font-semibold text-white hover:text-primary transition-colors">
                          {poll.title}
                        </h3>
                        <ArrowRight className="w-4 h-4 text-muted flex-shrink-0 mt-1" />
                      </div>
                      <p className="text-sm text-muted line-clamp-2">
                        {poll.description}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-muted">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          <span>{new Date(poll.created_at).toLocaleDateString()}</span>
                        </div>
                        {poll.your_vote_status && (
                          <div className="flex items-center gap-1">
                            <Vote className="w-3 h-3" />
                            <span>You voted</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="p-8 bg-surface border border-border rounded-lg text-center">
              <Vote className="w-12 h-12 text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">No proposals yet</h3>
              <p className="text-muted mb-4">Be the first to create a proposal for your community!</p>
              <Link to="/proposals/new">
                <Button variant="primary">
                  Create First Proposal
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
