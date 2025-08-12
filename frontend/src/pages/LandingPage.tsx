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
  CheckCircle
} from 'lucide-react';
import Button from '../components/ui/Button';

export default function LandingPage() {
  const features = [
    {
      icon: <Vote className="w-5 h-5" />,
      title: "Democratic Voting",
      description: "Participate in community decisions with transparent voting"
    },
    {
      icon: <MessageCircle className="w-5 h-5" />,
      title: "Community Discussion",
      description: "Engage in meaningful conversations with reactions"
    },
    {
      icon: <Users className="w-5 h-5" />,
      title: "Delegation System",
      description: "Delegate your vote to trusted community members"
    },
    {
      icon: <TrendingUp className="w-5 h-5" />,
      title: "Real-time Results",
      description: "See live voting results and engagement metrics"
    }
  ];

  const benefits = [
    "Strengthen local communities through active participation",
    "Make collective decisions more transparent and inclusive",
    "Build trust through democratic processes",
    "Empower community members to shape their shared future"
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

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Democracy for
              <span className="text-primary"> Communities</span>
            </h1>
            <p className="text-xl md:text-2xl text-muted mb-8 leading-relaxed max-w-3xl mx-auto">
              The Commons is a digital platform that reimagines how communities make decisions together. 
              Create proposals, vote on important matters, and build stronger communities through 
              transparent democratic processes.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/auth?mode=register">
                <Button size="lg" variant="primary" className="text-lg px-8 py-3">
                  Start Your Community
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

      {/* What is The Commons */}
      <section className="py-16 px-4 bg-surface/50">
        <div className="container mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              What is The Commons?
            </h2>
            <p className="text-lg text-muted max-w-3xl mx-auto leading-relaxed">
              The Commons is a democratic decision-making platform designed to strengthen local communities. 
              Whether you're part of a neighborhood association, local organization, or any community group, 
              we provide the tools you need to make collective decisions more effectively and inclusively.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="space-y-4"
            >
              <h3 className="text-xl font-semibold text-white mb-4">How it works</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-primary text-sm font-bold">1</span>
                  </div>
                  <p className="text-muted">Community members create proposals for important decisions</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-primary text-sm font-bold">2</span>
                  </div>
                  <p className="text-muted">Everyone can discuss, ask questions, and share perspectives</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-primary text-sm font-bold">3</span>
                  </div>
                  <p className="text-muted">Vote on proposals or delegate your vote to trusted members</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-primary text-sm font-bold">4</span>
                  </div>
                  <p className="text-muted">See transparent results and track community engagement</p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              viewport={{ once: true }}
              className="space-y-4"
            >
              <h3 className="text-xl font-semibold text-white mb-4">Why communities choose us</h3>
              <div className="space-y-3">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                    <p className="text-muted">{benefit}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Everything you need for community democracy
            </h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              Our platform combines modern democratic principles with intuitive technology, 
              making community decision-making accessible to everyone.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="p-6 bg-surface border border-border rounded-lg text-center hover:border-primary/50 transition-colors"
              >
                <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <div className="text-primary">
                    {feature.icon}
                  </div>
                </div>
                <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-muted">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-primary/10">
        <div className="container mx-auto text-center max-w-3xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Ready to strengthen your community?
            </h2>
            <p className="text-lg text-muted mb-8">
              Join The Commons today and start building a more democratic, 
              transparent, and engaged community.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/auth?mode=register">
                <Button size="lg" variant="primary" className="text-lg px-8 py-3">
                  Create Your Community
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/auth">
                <Button size="lg" variant="ghost" className="text-lg px-8 py-3">
                  Sign In to Existing Community
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-border">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs">C</span>
            </div>
            <span className="text-lg font-semibold text-white">The Commons</span>
          </div>
          <p className="text-muted text-sm">
            Empowering communities through democratic decision-making
          </p>
        </div>
      </footer>
    </div>
  );
}
