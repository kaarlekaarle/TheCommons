import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronDown } from 'lucide-react';
import type { Label } from '../types';
import { getLabelsCached } from '../lib/cache/labelsCache';
import { getTopicOverviewCached } from '../lib/cache/topicOverviewCache';
import { flags } from '../config/flags';

interface TopicsAutocompleteProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export const TopicsAutocomplete: React.FC<TopicsAutocompleteProps> = ({
  isOpen,
  onClose,
  className = ''
}) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [labels, setLabels] = useState<Label[]>([]);
  const [filteredLabels, setFilteredLabels] = useState<Label[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isLoadingRef = useRef(false);

  const fetchLabels = useCallback(async () => {
    // Prevent multiple simultaneous fetches
    if (isLoadingRef.current) {
      return;
    }

    // Abort previous request if it exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    setError(null);
    isLoadingRef.current = true;

    try {
      const labelsData = await getLabelsCached();
      setLabels(labelsData);
    } catch (err) {
      if (err && typeof err === 'object' && 'name' in err && err.name === 'AbortError') {
        return; // Request was aborted
      }
      setError('Failed to load topics');
      console.error('Error loading labels:', err);
    } finally {
      setIsLoading(false);
      isLoadingRef.current = false;
    }
  }, []);

  // Debounced search filter
  const debouncedFilter = useCallback(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      const filtered = labels.filter(label =>
        label.name.toLowerCase().includes(searchTerm.toLowerCase())
      ).slice(0, 6); // Top 6 results
      setFilteredLabels(filtered);
      setSelectedIndex(-1);
    }, 200);
  }, [labels, searchTerm]);

  // Memoize filtered results
  const memoizedFilteredLabels = useMemo(() => {
    return labels.filter(label =>
      label.name.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 6);
  }, [labels, searchTerm]);

  useEffect(() => {
    if (isOpen && flags.labelsEnabled) {
      fetchLabels();
      inputRef.current?.focus();
    }
  }, [isOpen, fetchLabels]);

  useEffect(() => {
    debouncedFilter();
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [debouncedFilter]);

  useEffect(() => {
    setFilteredLabels(memoizedFilteredLabels);
  }, [memoizedFilteredLabels]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < filteredLabels.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : filteredLabels.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && filteredLabels[selectedIndex]) {
          handleLabelSelect(filteredLabels[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
      case 'Tab':
        // Let Tab work normally for focus management
        break;
    }
  };

  const handleLabelSelect = (label: Label) => {
    // Prefetch the topic overview
    getTopicOverviewCached(label.slug);
    
    navigate(`/t/${label.slug}`);
    onClose();
    setSearchTerm('');
    setSelectedIndex(-1);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleOptionMouseEnter = (index: number) => {
    setSelectedIndex(index);
  };

  if (!flags.labelsEnabled) {
    return null;
  }

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Search topics..."
          className="w-full px-3 py-2 pl-10 pr-10 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:border-blue-500"
          aria-label="Search topics"
          aria-expanded={isOpen}
          aria-controls="topics-autocomplete-list"
          aria-activedescendant={selectedIndex >= 0 ? `topic-option-${selectedIndex}` : undefined}
          role="combobox"
          aria-autocomplete="list"
          aria-haspopup="listbox"
        />
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-xl z-50 max-h-64 overflow-hidden">
          {isLoading ? (
            <div className="px-4 py-3 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
                <span>Loading topics...</span>
              </div>
            </div>
          ) : error ? (
            <div className="px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          ) : filteredLabels.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-600">
              {searchTerm ? 'No topics found' : 'Type to search topics'}
            </div>
          ) : (
            <ul
              ref={listRef}
              id="topics-autocomplete-list"
              className="py-1"
              role="listbox"
            >
              {filteredLabels.map((label, index) => (
                <li
                  key={label.id}
                  id={`topic-option-${index}`}
                  className={`
                    px-4 py-2 text-sm cursor-pointer transition-colors
                    ${index === selectedIndex 
                      ? 'bg-blue-50 text-blue-900' 
                      : 'text-gray-700 hover:bg-gray-50'
                    }
                  `}
                  onClick={() => handleLabelSelect(label)}
                  onMouseEnter={() => handleOptionMouseEnter(index)}
                  role="option"
                  aria-selected={index === selectedIndex}
                >
                  {label.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default TopicsAutocomplete;
