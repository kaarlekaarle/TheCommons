import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

export default function PrincipleDiffPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const handleBack = () => {
    navigate(`/compass/${id}`);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="text-gray-700 hover:text-gray-900"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Principle
            </Button>
          </div>

          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
              Diff view (coming soon)
            </h1>
            <p className="text-gray-600">
              You'll be able to compare current vs proposed revisions side by side.
            </p>
          </div>
        </div>

        {/* Content */}
        <Card className="p-8">
          <div className="text-center space-y-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>

            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Diff View Feature
              </h2>
              <p className="text-gray-600 max-w-md mx-auto">
                This feature will allow you to see exactly what changes are being proposed
                and make informed decisions about accepting or rejecting revisions.
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex justify-center gap-4">
                <Button
                  variant="secondary"
                  disabled
                  className="opacity-50 cursor-not-allowed"
                >
                  Accept into Community
                </Button>
                <Button
                  variant="secondary"
                  disabled
                  className="opacity-50 cursor-not-allowed"
                >
                  Move to Counter
                </Button>
              </div>

              <p className="text-sm text-gray-500">
                TODO: Implement diff comparison and action buttons
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
