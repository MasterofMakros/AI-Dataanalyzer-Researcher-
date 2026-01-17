'use client';

import { useEffect, useCallback, useState } from 'react';
import { useTheme } from 'next-themes';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  description: string;
  category: 'navigation' | 'actions' | 'sources' | 'other';
}

export const KEYBOARD_SHORTCUTS: KeyboardShortcut[] = [
  { key: '/', description: 'Focus search input', category: 'navigation' },
  { key: 'Escape', description: 'Close modal/dialog', category: 'navigation' },
  { key: '?', description: 'Show keyboard shortcuts', category: 'other' },
  { key: 'n', ctrl: true, description: 'New chat', category: 'actions' },
  { key: 'c', ctrl: true, shift: true, description: 'Copy answer', category: 'actions' },
  { key: 'e', ctrl: true, description: 'Export chat', category: 'actions' },
  { key: 't', description: 'Toggle theme', category: 'other' },
  { key: '1', description: 'Open source 1', category: 'sources' },
  { key: '2', description: 'Open source 2', category: 'sources' },
  { key: '3', description: 'Open source 3', category: 'sources' },
  { key: '4', description: 'Open source 4', category: 'sources' },
  { key: '5', description: 'Open source 5', category: 'sources' },
  { key: '6', description: 'Open source 6', category: 'sources' },
  { key: '7', description: 'Open source 7', category: 'sources' },
  { key: '8', description: 'Open source 8', category: 'sources' },
  { key: '9', description: 'Open source 9', category: 'sources' },
];

interface UseKeyboardShortcutsOptions {
  onOpenHelp?: () => void;
  onCloseModal?: () => void;
  onNewChat?: () => void;
  onCopyAnswer?: () => void;
  onExport?: () => void;
  onOpenSource?: (index: number) => void;
  onToggleTheme?: () => void;
  enabled?: boolean;
}

export function useKeyboardShortcuts(options: UseKeyboardShortcutsOptions = {}) {
  const {
    onOpenHelp,
    onCloseModal,
    onNewChat,
    onCopyAnswer,
    onExport,
    onOpenSource,
    onToggleTheme,
    enabled = true,
  } = options;

  const { theme, setTheme } = useTheme();
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;

      const activeElement = document.activeElement;
      const isInputFocused =
        activeElement?.tagName === 'INPUT' ||
        activeElement?.tagName === 'TEXTAREA' ||
        activeElement?.hasAttribute('contenteditable');

      // Always handle Escape
      if (e.key === 'Escape') {
        e.preventDefault();
        if (isHelpOpen) {
          setIsHelpOpen(false);
        }
        onCloseModal?.();
        return;
      }

      // Don't handle other shortcuts when input is focused
      if (isInputFocused) return;

      // ? - Show help
      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault();
        setIsHelpOpen(true);
        onOpenHelp?.();
        return;
      }

      // t - Toggle theme
      if (e.key === 't' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        onToggleTheme?.();
        return;
      }

      // Ctrl+N - New chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        onNewChat?.();
        window.location.href = '/';
        return;
      }

      // Ctrl+Shift+C - Copy answer
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
        e.preventDefault();
        onCopyAnswer?.();
        return;
      }

      // Ctrl+E - Export
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        onExport?.();
        return;
      }

      // 1-9 - Open source
      if (/^[1-9]$/.test(e.key)) {
        e.preventDefault();
        const index = parseInt(e.key, 10) - 1;
        onOpenSource?.(index);
        return;
      }
    },
    [
      enabled,
      isHelpOpen,
      theme,
      setTheme,
      onOpenHelp,
      onCloseModal,
      onNewChat,
      onCopyAnswer,
      onExport,
      onOpenSource,
      onToggleTheme,
    ]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  return {
    isHelpOpen,
    setIsHelpOpen,
    shortcuts: KEYBOARD_SHORTCUTS,
  };
}

export default useKeyboardShortcuts;
