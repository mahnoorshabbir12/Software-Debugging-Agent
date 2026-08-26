import React, { useEffect, useState } from 'react';
import './Toast.css';

interface ToastProps {
  message: string;
  type?: 'info' | 'success' | 'error';
}

export const Toast: React.FC<ToastProps> = ({ message, type = 'info' }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), 4000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible || !message) return null;

  return (
    <div className={`toast toast-${type}`}>
      {message}
    </div>
  );
};
