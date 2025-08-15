import React from 'react';
import { principlesCopy } from '../../copy/principles';

interface TabSwitcherProps {
  activeTab: 'revisions' | 'discussion';
  onTabChange: (tab: 'revisions' | 'discussion') => void;
}

export default function TabSwitcher({ activeTab, onTabChange }: TabSwitcherProps) {
  const handleKeyDown = (e: React.KeyboardEvent, tab: 'revisions' | 'discussion') => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onTabChange(tab);
    }
  };

  const handleTabChange = (tab: 'revisions' | 'discussion') => {
    onTabChange(tab);
    // Analytics: principles_view_switched
    console.log('principles_view_switched', { view: tab });
  };

  return (
    <div className="border-b border-gray-200" role="tablist">
      <div className="flex">
        {(['revisions', 'discussion'] as const).map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            aria-controls={`${tab}-panel`}
            onClick={() => handleTabChange(tab)}
            onKeyDown={(e) => handleKeyDown(e, tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              activeTab === tab
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            data-testid={`${tab}-tab`}
          >
            {tab === 'revisions' ? principlesCopy.subviews.revisions : principlesCopy.subviews.discussion}
          </button>
        ))}
      </div>
    </div>
  );
}
