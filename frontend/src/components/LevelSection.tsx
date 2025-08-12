import React from 'react';
import { Compass, Target } from 'lucide-react';

interface LevelSectionProps {
  level: 'a' | 'b';
  title: string;
  children: React.ReactNode;
  className?: string;
}

export default function LevelSection({ level, title, children, className = '' }: LevelSectionProps) {
  const isLevelA = level === 'a';
  const icon = isLevelA ? <Compass className="w-5 h-5" /> : <Target className="w-5 h-5" />;
  const helperText = isLevelA 
    ? "Sets the compass. Guides all other decisions."
    : "Moves us forward now. Adjusts as needed.";

  // Color schemes for different levels
  const levelAClasses = {
    iconBg: "bg-gov-primary/10",
    iconColor: "text-gov-primary",
    titleColor: "text-gov-primary",
    helperColor: "text-gov-text-muted"
  };
  
  const levelBClasses = {
    iconBg: "bg-gov-secondary/10",
    iconColor: "text-gov-secondary",
    titleColor: "text-gov-secondary",
    helperColor: "text-gov-text-muted"
  };
  
  const classes = isLevelA ? levelAClasses : levelBClasses;

  return (
    <section className={`space-y-6 ${className}`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${classes.iconBg}`}>
          <div className={classes.iconColor}>
            {icon}
          </div>
        </div>
        <div>
          <h2 className={`text-xl font-semibold ${classes.titleColor}`}>{title}</h2>
          <p className={`text-sm ${classes.helperColor}`}>{helperText}</p>
        </div>
      </div>
      {children}
    </section>
  );
}
