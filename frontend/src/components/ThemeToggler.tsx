import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export const ThemeToggler: React.FC = () => {
  const { mode, toggleMode } = useTheme();

  return (
    <button
      onClick={toggleMode}
      className="theme-toggler flex items-center justify-center p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
      aria-label="Toggle theme mode"
      title={`Switch to ${mode === 'light' ? 'dark' : 'light'} mode`}
    >
      {mode === 'light' ? (
        <Moon className="w-5 h-5 text-secondary" />
      ) : (
        <Sun className="w-5 h-5 text-accent" />
      )}
    </button>
  );
};
