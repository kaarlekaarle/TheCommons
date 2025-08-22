import React, { forwardRef, useEffect, useRef } from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  className?: string;
}

const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ className = '', rows = 3, value, onChange, ...props }, ref) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const resizeTimeoutRef = useRef<number | null>(null);

    // Combine refs
    const combinedRef = (node: HTMLTextAreaElement) => {
      textareaRef.current = node;
      if (typeof ref === 'function') {
        ref(node);
      } else if (ref) {
        ref.current = node;
      }
    };

    const adjustHeight = () => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';

      // Calculate new height based on content
      const computedStyle = window.getComputedStyle(textarea);
      const lineHeight = parseInt(computedStyle.lineHeight) || 20;
      const paddingTop = parseInt(computedStyle.paddingTop) || 0;
      const paddingBottom = parseInt(computedStyle.paddingBottom) || 0;
      const borderTop = parseInt(computedStyle.borderTopWidth) || 0;
      const borderBottom = parseInt(computedStyle.borderBottomWidth) || 0;

      const minHeight = lineHeight * rows + paddingTop + paddingBottom + borderTop + borderBottom;
      const scrollHeight = textarea.scrollHeight;

      textarea.style.height = `${Math.max(minHeight, scrollHeight)}px`;
    };

    useEffect(() => {
      if (resizeTimeoutRef.current) {
        cancelAnimationFrame(resizeTimeoutRef.current);
      }

      resizeTimeoutRef.current = requestAnimationFrame(adjustHeight);

      return () => {
        if (resizeTimeoutRef.current) {
          cancelAnimationFrame(resizeTimeoutRef.current);
        }
      };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional one-time height adjustment
    }, [value]);

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange?.(e);
    };

    return (
      <textarea
        ref={combinedRef}
        className={`p-3 border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors placeholder-gray-500 ${className}`}
        rows={rows}
        value={value}
        onChange={handleChange}
        {...props}
      />
    );
  }
);

TextArea.displayName = 'TextArea';

export default TextArea;
