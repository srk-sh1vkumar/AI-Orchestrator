/**
 * TagEditor Component
 *
 * Enhancement 022: Add/remove tags from conversations with autocomplete
 */

import React, { useState, useRef, useEffect } from 'react';
import { Tag, X, Plus } from 'lucide-react';
import axios from 'axios';

interface TagEditorProps {
  conversationId: string;
  initialTags: string[];
  availableTags: string[];
  onTagsUpdate: (tags: string[]) => void;
}

export const TagEditor: React.FC<TagEditorProps> = ({
  conversationId,
  initialTags,
  availableTags,
  onTagsUpdate,
}) => {
  const [tags, setTags] = useState<string[]>(initialTags);
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter suggestions based on input
  const suggestions = availableTags
    .filter(
      (tag) =>
        !tags.includes(tag) &&
        tag.toLowerCase().includes(inputValue.toLowerCase())
    )
    .slice(0, 5);

  // Predefined common tags
  const commonTags = ['work', 'debug', 'research', 'production', 'personal'];

  const addTag = async (tag: string) => {
    const trimmedTag = tag.trim().toLowerCase();
    if (!trimmedTag || tags.includes(trimmedTag)) return;

    setIsLoading(true);
    try {
      await axios.post(
        `http://localhost:8000/api/conversations/${conversationId}/tags`,
        [trimmedTag]
      );

      const updatedTags = [...tags, trimmedTag];
      setTags(updatedTags);
      onTagsUpdate(updatedTags);
      setInputValue('');
      setShowSuggestions(false);
    } catch (error) {
      console.error('Failed to add tag:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const removeTag = async (tagToRemove: string) => {
    setIsLoading(true);
    try {
      await axios.delete(
        `http://localhost:8000/api/conversations/${conversationId}/tags`,
        { data: [tagToRemove] }
      );

      const updatedTags = tags.filter((tag) => tag !== tagToRemove);
      setTags(updatedTags);
      onTagsUpdate(updatedTags);
    } catch (error) {
      console.error('Failed to remove tag:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  return (
    <div className="relative">
      {/* Existing Tags */}
      <div className="flex flex-wrap gap-2 mb-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm"
          >
            <Tag className="w-3 h-3" />
            {tag}
            <button
              onClick={() => removeTag(tag)}
              disabled={isLoading}
              className="hover:bg-blue-200 dark:hover:bg-blue-800 rounded-full p-0.5 transition-colors disabled:opacity-50"
              aria-label={`Remove tag ${tag}`}
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>

      {/* Add Tag Input */}
      <div className="relative">
        <div className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800">
          <Plus className="w-4 h-4 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              setShowSuggestions(e.target.value.length > 0);
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => inputValue.length > 0 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="Add tag..."
            className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400 text-sm"
            disabled={isLoading}
          />
        </div>

        {/* Autocomplete Suggestions */}
        {showSuggestions && (suggestions.length > 0 || commonTags.length > 0) && (
          <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
            {/* Common Tags */}
            {!inputValue && commonTags.filter(t => !tags.includes(t)).length > 0 && (
              <div className="p-2 border-b border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Common tags
                </p>
                <div className="flex flex-wrap gap-1">
                  {commonTags
                    .filter((tag) => !tags.includes(tag))
                    .map((tag) => (
                      <button
                        key={tag}
                        onClick={() => addTag(tag)}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded text-xs text-gray-700 dark:text-gray-300 transition-colors"
                      >
                        {tag}
                      </button>
                    ))}
                </div>
              </div>
            )}

            {/* Matching Suggestions */}
            {suggestions.length > 0 && (
              <div className="p-1">
                <p className="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                  Suggestions
                </p>
                {suggestions.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => addTag(tag)}
                    className="w-full px-2 py-1.5 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                  >
                    <Tag className="w-3 h-3 inline mr-1" />
                    {tag}
                  </button>
                ))}
              </div>
            )}

            {/* Create New Tag */}
            {inputValue && !suggestions.includes(inputValue.trim().toLowerCase()) && (
              <div className="p-1 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => addTag(inputValue)}
                  className="w-full px-2 py-1.5 text-left text-sm text-blue-600 dark:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  <Plus className="w-3 h-3 inline mr-1" />
                  Create "{inputValue.trim().toLowerCase()}"
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
