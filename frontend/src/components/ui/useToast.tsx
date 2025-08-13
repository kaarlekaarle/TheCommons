import { useToaster } from './use-toaster';

export function useToast() {
  const { addToast, removeToast } = useToaster();
  
  return {
    success: (message: string) => addToast({ type: 'success', message }),
    error: (message: string) => addToast({ type: 'error', message }),
    info: (message: string) => addToast({ type: 'info', message }),
    remove: removeToast,
  };
}
