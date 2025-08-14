import React from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
}

export default function SectionHeader({ title, subtitle }: SectionHeaderProps) {
  return (
    <div className="mb-3">
      <h2 className="text-strong text-xl md:text-2xl font-semibold">{title}</h2>
      {subtitle && <p className="text-subtle text-sm md:text-base mt-1">{subtitle}</p>}
    </div>
  );
}
