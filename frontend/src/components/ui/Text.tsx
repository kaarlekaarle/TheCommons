import React from 'react';

interface TextProps {
  as?: React.ElementType;
  children: React.ReactNode;
  muted?: boolean;
  className?: string;
  [key: string]: any;
}

export function Text({ 
  as: Comp = 'p', 
  children, 
  muted = false, 
  className = '', 
  ...rest 
}: TextProps) {
  return (
    <Comp 
      className={`${muted ? 'text-muted' : 'text-body'} ${className}`} 
      {...rest}
    >
      {children}
    </Comp>
  );
}
