import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Vote, 
  MessageCircle, 
  Users, 
  TrendingUp, 
  Shield, 
  Globe,
  ArrowRight,
  CheckCircle,
  Heart,
  Sparkles,
  Handshake,
  Lightbulb
} from 'lucide-react';
import Button from '../components/ui/Button';

export default function LandingPage() {
  const communityStories = [
    {
      icon: <Heart className="w-6 h-6" />,
      title: "Park Project",
      description: "From an empty lot to a meeting place — decided together."
    },
    {
      icon: <Handshake className="w-6 h-6" />,
      title: "Business Alliance",
      description: "Shops agreed on a shared plan that boosted the street."
    },
    {
      icon: <Lightbulb className="w-6 h-6" />,
      title: "Community Garden",
      description: "Families worked together to grow food for the neighbourhood."
    }
  ];

  const waysToConnect = [
    {
      icon: <Vote className="w-5 h-5" />,
      title: "Propose & Vote",
      description: "Put forward an idea or vote on what matters now."
    },
    {
      icon: <MessageCircle className="w-5 h-5" />,
      title: "Talk It Through",
      description: "Share arguments and comments before the vote."
    },
    {
      icon: <Users className="w-5 h-5" />,
      title: "Delegate When Needed",
      description: "Pass your vote to someone you trust, take it back anytime."
    },
    {
      icon: <TrendingUp className="w-5 h-5" />,
      title: "See the Result",
      description: "Outcomes and reasoning are public."
    }
  ];

  const benefits = [
    "Agree on principles first, then decide on actions.",
    "Keep urgent decisions from overriding shared values.",
    "Make debates clearer by knowing which choice you're making.",
    "Build a record of where the community stands."
  ];

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-bold text-white">The Commons</span>
            </div>
            <div className="flex items-center space-x-3">
              <Link to="/auth">
                <Button variant="ghost" size="sm">
                  Log In
                </Button>
              </Link>
              <Link to="/auth?mode=register">
                <Button variant="primary" size="sm">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section - Warm and Aspirational */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Decisions We Make Together
            </h1>
            <p className="text-xl md:text-2xl text-muted mb-8 leading-relaxed max-w-3xl mx-auto">
              The Commons is where communities decide their future — openly, fairly, and together. 
              It's built on the idea that everyone should have a voice and every decision should be clear and accountable.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/auth?mode=register">
                <Button size="lg" variant="primary" className="text-lg px-8 py-3">
                  Join Your Community
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/auth">
                <Button size="lg" variant="ghost" className="text-lg px-8 py-3">
                  Sign In
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Community Stories Section */}
      <section className="py-16 px-4 bg-surface/50">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              From Ideas to Action
            </h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              How communities have turned discussion into real change
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {communityStories.map((story, index) => (
              <motion.div
                key={story.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.2 }}
                className="p-6 bg-surface border border-border rounded-lg text-center"
              >
                <div className="text-primary mb-4 flex justify-center">
                  {story.icon}
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">{story.title}</h3>
                <p className="text-muted">{story.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section - Human-Centered */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              How It Works
            </h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              Simple tools that make community decision-making accessible to everyone
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {waysToConnect.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-6 bg-surface border border-border rounded-lg text-center"
              >
                <div className="text-primary mb-4 flex justify-center">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-muted">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-16 px-4 bg-surface/50">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Why Two Levels?
            </h2>
            <p className="text-lg text-muted">
              Build stronger, more connected communities through democratic participation
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {benefits.map((benefit, index) => (
              <motion.div
                key={benefit}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-3"
              >
                <CheckCircle className="w-5 h-5 text-primary flex-shrink-0 mt-1" />
                <span className="text-muted">{benefit}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto text-center max-w-3xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Your Voice Belongs Here
            </h2>
            <p className="text-lg text-muted mb-8">
              Start shaping your community's decisions today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/auth?mode=register">
                <Button size="lg" variant="primary" className="text-lg px-8 py-3">
                  Start Now
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/why">
                <Button size="lg" variant="ghost" className="text-lg px-8 py-3">
                  Learn More
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-4">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs">C</span>
            </div>
            <span className="text-lg font-bold text-white">The Commons</span>
          </div>
          <p className="text-muted mb-4">
            Deciding together, openly.
          </p>
          <div className="flex justify-center space-x-6 text-sm">
            <Link to="/why" className="text-muted hover:text-white transition-colors">
              Why Two Levels?
            </Link>
            <Link to="/auth" className="text-muted hover:text-white transition-colors">
              Sign In
            </Link>
            <Link to="/auth?mode=register" className="text-muted hover:text-white transition-colors">
              Get Started
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
