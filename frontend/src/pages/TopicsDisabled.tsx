import React from 'react';
import { Link } from 'react-router-dom';

export default function TopicsDisabled() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Topics Are Not Available</h1>
        <p className="text-gray-600 mb-6">
          The topics feature is not available right now. You can still explore principles and actions, or share your own ideas.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/principles"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            Browse Principles
          </Link>
          <Link
            to="/actions"
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
          >
            Browse Actions
          </Link>
          <Link
            to="/proposals/new"
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors"
          >
            Share Your Idea
          </Link>
        </div>
      </div>
    </main>
  );
}
