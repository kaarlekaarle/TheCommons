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
  BarChart3,
  Heart,
  Sparkles,
  Handshake,
  Lightbulb
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

  const communityStories = [
    {
      icon: <Heart className="w-6 h-6" />,
      title: "Neighborhood Park Project",
      description: "Residents came together to transform an empty lot into a vibrant community space"
    },
    {
      icon: <Handshake className="w-6 h-6" />,
      title: "Local Business Alliance",
      description: "Shop owners collaborated to create a shared marketing campaign that boosted everyone's sales"
    },
    {
      icon: <Lightbulb className="w-6 h-6" />,
      title: "Community Garden Initiative",
      description: "Families worked together to establish sustainable food sources for the neighborhood"
    }
  ];

  const waysToParticipate = [
    {
      icon: <Vote className="w-6 h-6" />,
      title: "Share Your Voice",
      description: "Cast your vote on decisions that shape your community's future"
    },
    {
      icon: <MessageCircle className="w-6 h-6" />,
      title: "Join the Conversation",
      description: "Share ideas, ask questions, and connect with your neighbors"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Build Trust Together",
      description: "Delegate your voice to community members you trust and respect"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "See Your Impact",
      description: "Watch how your participation helps build a stronger community"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Safe & Transparent",
      description: "Every decision is open and accountable to build lasting trust"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Local to Global",
      description: "Start with your neighborhood, inspire communities everywhere"
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section - Warm and Aspirational */}
      <div className="text-center mb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-warm"
        >
          <h1 className="gradient-text text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Welcome to the Commons
          </h1>
          <p className="text-xl text-muted-300 max-w-3xl mx-auto leading-relaxed">
            Here's where ideas are shared, debated, and decided. Every voice matters — and every decision is public.
          </p>
        </motion.div>
      </div>

      <div className="grid gap-12 lg:grid-cols-2">
        {/* Left Column - Community Focus */}
        <div className="space-warm">
          {/* About Section - Human-Centered */}
          <section className="card animate-warm-in">
            <div className="card-header">
              <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-primary-400 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                About The Commons
              </h2>
            </div>
            <div className="card-content space-warm">
              <p className="text-muted-300 leading-relaxed">
                The Commons is an open space for making community decisions.
              </p>
              <p className="text-muted-300 leading-relaxed">
                We keep principles (Level A) separate from immediate actions (Level B), so we don't confuse long-term direction with short-term steps.
              </p>
              <p className="text-muted-300 leading-relaxed">
                You can propose, discuss, vote, or delegate. Everything is transparent and reversible.
              </p>
            </div>
          </section>

          {/* Community Stories - Inspiring Examples */}
          <section className="space-warm">
            <h2 className="text-2xl font-semibold text-white mb-8">Community Success Stories</h2>
            <div className="space-inclusive">
              {communityStories.map((story, index) => (
                <motion.div
                  key={story.title}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="card hover:shadow-warm"
                >
                  <div className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-primary-400 rounded-xl flex items-center justify-center flex-shrink-0">
                        {story.icon}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-2">{story.title}</h3>
                        <p className="text-muted-300 leading-relaxed">{story.description}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </section>

          {/* Ways to Participate - Empowering Language */}
          <section className="space-warm">
            <h2 className="text-2xl font-semibold text-white mb-8">Ways to Participate</h2>
            <div className="grid gap-6 sm:grid-cols-2">
              {waysToParticipate.map((way, index) => (
                <motion.div
                  key={way.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="card hover:shadow-warm"
                >
                  <div className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-primary-400 rounded-xl flex items-center justify-center flex-shrink-0">
                        {way.icon}
                      </div>
                      <div>
                        <h3 className="font-semibold text-white mb-2">{way.title}</h3>
                        <p className="text-sm text-muted-300 leading-relaxed">{way.description}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </section>

          {/* Quick Actions - Inviting Language */}
          <section className="card animate-warm-in">
            <div className="card-header">
              <h2 className="text-xl font-semibold text-white mb-4">Ready to Get Started?</h2>
            </div>
            <div className="card-content space-warm">
              <Link to="/proposals/new">
                <Button className="w-full justify-start" variant="primary" size="lg">
                  <Lightbulb className="w-5 h-5 mr-3" />
                  Start a Proposal
                </Button>
              </Link>
              <Link to="/proposals">
                <Button className="w-full justify-start" variant="secondary" size="lg">
                  <BarChart3 className="w-5 h-5 mr-3" />
                  See Proposals
                </Button>
              </Link>
              <Link to="/activity">
                <Button className="w-full justify-start" variant="ghost" size="lg">
                  <TrendingUp className="w-5 h-5 mr-3" />
                  Community Activity
                </Button>
              </Link>
            </div>
          </section>
        </div>

        {/* Right Column - Recent Community Activity */}
        <div className="space-warm">
          <section>
            <h2 className="text-2xl font-semibold text-white mb-8">Latest Decisions & Discussions</h2>
            {loading ? (
              <div className="space-warm">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="card animate-pulse">
                    <div className="p-6">
                      <div className="h-4 bg-muted-600 rounded mb-3"></div>
                      <div className="h-3 bg-muted-600 rounded w-3/4"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : recentPolls.length > 0 ? (
              <div className="space-warm">
                {recentPolls.map((poll, index) => (
                  <motion.div
                    key={poll.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="card hover:shadow-warm"
                  >
                    <Link to={`/proposals/${poll.id}`}>
                      <div className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-semibold text-white mb-2 hover:text-primary-300 transition-colors">
                              {poll.title}
                            </h3>
                            <p className="text-sm text-muted-300 line-clamp-2 mb-4 leading-relaxed">
                              {poll.description}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-muted-400">
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(poll.created_at).toLocaleDateString()}
                              </span>
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                Community Member
                              </span>
                            </div>
                          </div>
                          <ArrowRight className="w-4 h-4 text-muted-400 flex-shrink-0 mt-1" />
                        </div>
                      </div>
                    </Link>
                  </motion.div>
                ))}
                <div className="text-center pt-6">
                  <Link to="/proposals">
                    <Button variant="secondary" className="text-primary-400 hover:text-primary-300">
                      See All Proposals
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="card text-center animate-warm-in">
                <div className="p-12">
                  <div className="w-16 h-16 bg-gradient-to-r from-primary-500 to-primary-400 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <Users className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">Be the First!</h3>
                  <p className="text-muted-300 mb-6 leading-relaxed">
                    No proposals yet. Start the conversation by sharing your first idea with the community.
                  </p>
                  <Link to="/proposals/new">
                    <Button variant="primary" size="lg">
                      <Lightbulb className="w-5 h-5 mr-2" />
                      start one now.
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
