import { useContext } from 'react';
import { ToastContext } from './toast-context-definition';

export const useToaster = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToaster must be used within a ToasterProvider');
  }
  return context;
};
