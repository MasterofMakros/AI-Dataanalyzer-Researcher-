'use client';

import React from 'react';

interface PreviewCardProps {
  href?: string;
  onClick?: () => void;
  testId?: string;
  children: React.ReactNode;
  className?: string;
}

const PreviewCard = ({
  href,
  onClick,
  testId,
  children,
  className,
}: PreviewCardProps) => {
  const baseClasses =
    'bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 font-medium';

  if (onClick) {
    return (
      <button
        type="button"
        className={`${baseClasses} ${className ?? ''}`}
        onClick={onClick}
        data-testid={testId}
      >
        {children}
      </button>
    );
  }

  if (href) {
    return (
      <a
        className={`${baseClasses} ${className ?? ''}`}
        href={href}
        target="_blank"
        rel="noreferrer"
        data-testid={testId}
      >
        {children}
      </a>
    );
  }

  return (
    <div className={`${baseClasses} ${className ?? ''}`} data-testid={testId}>
      {children}
    </div>
  );
};

export default PreviewCard;
