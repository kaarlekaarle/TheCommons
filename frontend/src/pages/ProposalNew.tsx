import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import api from '../lib/api';
import { useToast } from '../components/ui/useToast';
import Button from '../components/ui/Button';

export default function ProposalNew() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'General'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/polls/', {
        title: formData.title,
        description: formData.description
      });

      success('Proposal created successfully');
      
      // Navigate to proposal detail page
      navigate(`/proposals/${response.data.id}`);
    } catch (err: unknown) {
      const error = err as { response?: { status?: number; data?: { detail?: string } }; message?: string };
      if (error.response?.status === 401) {
        // Redirect to login
        navigate('/login');
      } else {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to create proposal';
        setError(errorMessage);
        showError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Link to="/proposals" className="text-muted hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-3xl font-bold">Create New Proposal</h1>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-muted mb-1">
            Title *
          </label>
          <input
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({...formData, title: e.target.value})}
            className="w-full px-3 py-2 bg-bg border border-border rounded-md text-white placeholder-muted focus:ring-2 focus:ring-primary/50 focus:border-transparent"
            placeholder="Enter proposal title"
            required
          />
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-muted mb-1">
            Description *
          </label>
          <textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            rows={6}
            className="w-full px-3 py-2 bg-bg border border-border rounded-md text-white placeholder-muted focus:ring-2 focus:ring-primary/50 focus:border-transparent resize-none"
            placeholder="Describe your proposal in detail..."
            required
          />
        </div>

        {error && (
          <div className="p-3 bg-danger/10 border border-danger/20 rounded-md">
            <p className="text-sm text-danger">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <Button
            type="submit"
            loading={loading}
            className="flex-1"
          >
            Create Proposal
          </Button>
          <Link to="/proposals">
            <Button
              type="button"
              variant="ghost"
            >
              Cancel
            </Button>
          </Link>
        </div>
      </form>
    </div>
  );
}
