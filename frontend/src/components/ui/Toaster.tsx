import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ToasterProvider as BaseToasterProvider } from './toast-context';
import { useToaster } from './use-toaster';

export { ToasterProvider as BaseToasterProvider } from './toast-context';
export type { Toast } from './toast-context-definition';

export const ToasterProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <BaseToasterProvider>
      {children}
      <Toaster />
    </BaseToasterProvider>
  );
};

const Toaster = () => {
  const { toasts, removeToast } = useToaster();

  const getToastStyles = (type: 'success' | 'error' | 'info' | 'warning') => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getIcon = (type: 'success' | 'error' | 'info' | 'warning') => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'info':
        return 'ℹ';
      default:
        return '•';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      <AnimatePresence>
        {toasts.map((toast, index) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 300, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 300, scale: 0.95 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className={`max-w-sm w-full p-4 rounded-lg border shadow-lg ${getToastStyles(toast.type)}`}
            style={{ zIndex: 1000 - index }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-current bg-opacity-20 text-sm font-medium">
                  {getIcon(toast.type)}
                </span>
                <p className="text-sm font-medium">{toast.message}</p>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="flex-shrink-0 ml-4 text-current opacity-60 hover:opacity-100 transition-opacity"
              >
                <span className="sr-only">Close</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};
