/**
 * ConversationSearch Component
 *
 * Enhancement 022: Full-text search across conversation history
 * with keyboard shortcuts and debounced API calls.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Search, X, Filter } from 'lucide-react';

interface ConversationSearchProps {
  onSearch: (query: string) => void;
  onFilterToggle: () => void;
  placeholder?: string;
  showFilters?: boolean;
}

export const ConversationSearch: React.FC<ConversationSearchProps> = ({
  onSearch,
  onFilterToggle,
  placeholder = "Search conversations...",
  showFilters = false,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  // Debounced search - wait 300ms after user stops typing
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      onSearch(searchQuery);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchQuery, onSearch]);

  // Keyboard shortcut: Cmd/Ctrl + F
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.getElementById('conversation-search') as HTMLInputElement;
        searchInput?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleClear = useCallback(() => {
    setSearchQuery('');
    onSearch('');
  }, [onSearch]);

  return (
    <div className="relative w-full">
      <div
        className={`flex items-center gap-2 px-4 py-2 border rounded-lg transition-all ${
          isFocused
            ? 'border-blue-500 ring-2 ring-blue-500 ring-opacity-20'
            : 'border-gray-300 dark:border-gray-600'
        } bg-white dark:bg-gray-800`}
      >
        <Search className="w-5 h-5 text-gray-400" />

        <input
          id="conversation-search"
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400"
        />

        {searchQuery && (
          <button
            onClick={handleClear}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            aria-label="Clear search"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}

        <button
          onClick={onFilterToggle}
          className={`p-2 rounded transition-colors ${
            showFilters
              ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
          }`}
          aria-label="Toggle filters"
        >
          <Filter className="w-4 h-4" />
        </button>
      </div>

      {/* Keyboard shortcut hint */}
      <div className="absolute right-2 top-full mt-1 text-xs text-gray-400 dark:text-gray-500">
        Press <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">⌘/Ctrl</kbd>
        {' + '}
        <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">F</kbd>
        {' to search'}
      </div>
    </div>
  );
};
