import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export default function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`p-6 bg-surface border border-border rounded-lg ${className}`}>
      {children}
    </div>
  );
}
