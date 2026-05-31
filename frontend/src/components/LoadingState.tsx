/**
 * LoadingState Component
 *
 * Enhancement 022: Skeleton loaders for async data
 * Prevents blank screens during loading
 */

import React from 'react';

interface LoadingStateProps {
  type?: 'conversation' | 'message' | 'list' | 'card';
  count?: number;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  type = 'list',
  count = 3,
}) => {
  switch (type) {
    case 'conversation':
      return <ConversationSkeleton />;
    case 'message':
      return <MessageSkeleton count={count} />;
    case 'card':
      return <CardSkeleton count={count} />;
    case 'list':
    default:
      return <ListSkeleton count={count} />;
  }
};

/**
 * Skeleton for conversation list items
 */
const ListSkeleton: React.FC<{ count: number }> = ({ count }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg animate-pulse"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

/**
 * Skeleton for chat messages
 */
const MessageSkeleton: React.FC<{ count: number }> = ({ count }) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'} animate-pulse`}
      >
        <div
          className={`max-w-lg p-4 rounded-lg ${
            i % 2 === 0
              ? 'bg-gray-200 dark:bg-gray-700'
              : 'bg-blue-100 dark:bg-blue-900'
          }`}
        >
          <div className="space-y-2">
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-full" />
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-5/6" />
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-4/6" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

/**
 * Skeleton for full conversation view
 */
const ConversationSkeleton: React.FC = () => (
  <div className="flex flex-col h-full animate-pulse">
    {/* Header */}
    <div className="p-4 border-b border-gray-200 dark:border-gray-700">
      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2" />
      <div className="flex gap-2">
        <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded-full w-16" />
        <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded-full w-16" />
      </div>
    </div>

    {/* Messages */}
    <div className="flex-1 p-4 space-y-4 overflow-y-auto">
      <MessageSkeleton count={5} />
    </div>

    {/* Input */}
    <div className="p-4 border-t border-gray-200 dark:border-gray-700">
      <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
    </div>
  </div>
);

/**
 * Skeleton for card layout
 */
const CardSkeleton: React.FC<{ count: number }> = ({ count }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg animate-pulse"
      >
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-5/6" />
          <div className="flex gap-2 mt-4">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-16" />
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-16" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

/**
 * Inline loading spinner
 */
export const Spinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div
      className={`${sizeClasses[size]} border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin`}
      role="status"
      aria-label="Loading"
    />
  );
};

/**
 * Full-page loading overlay
 */
export const LoadingOverlay: React.FC<{ message?: string }> = ({
  message = 'Loading...',
}) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 flex flex-col items-center gap-4">
      <Spinner size="lg" />
      <p className="text-gray-900 dark:text-gray-100">{message}</p>
    </div>
  </div>
);
