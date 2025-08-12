import { useToaster } from './Toaster';

export const useToast = () => {
  const { addToast } = useToaster();

  return {
    success: (message: string, duration?: number) => 
      addToast({ type: 'success', message, duration: duration || 3000 }),
    error: (message: string, duration?: number) => 
      addToast({ type: 'error', message, duration: duration || 6000 }),
    info: (message: string, duration?: number) => 
      addToast({ type: 'info', message, duration: duration || 4000 }),
  };
};
