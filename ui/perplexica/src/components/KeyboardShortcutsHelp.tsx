'use client';

import { Fragment } from 'react';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import { X, Keyboard } from 'lucide-react';
import { KEYBOARD_SHORTCUTS, KeyboardShortcut } from '@/lib/hooks/useKeyboardShortcuts';

interface KeyboardShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

const ShortcutKey = ({ shortcut }: { shortcut: KeyboardShortcut }) => {
  const keys: string[] = [];

  if (shortcut.ctrl) {
    keys.push('Ctrl');
  }
  if (shortcut.shift) {
    keys.push('Shift');
  }
  if (shortcut.alt) {
    keys.push('Alt');
  }
  keys.push(shortcut.key === ' ' ? 'Space' : shortcut.key.toUpperCase());

  return (
    <div className="flex items-center gap-1">
      {keys.map((key, index) => (
        <Fragment key={key}>
          <kbd className="px-2 py-1 text-xs font-semibold text-black/80 dark:text-white/80 bg-light-200 dark:bg-dark-200 border border-light-300 dark:border-dark-300 rounded shadow-sm min-w-[24px] text-center">
            {key}
          </kbd>
          {index < keys.length - 1 && (
            <span className="text-black/40 dark:text-white/40">+</span>
          )}
        </Fragment>
      ))}
    </div>
  );
};

const ShortcutGroup = ({
  title,
  shortcuts,
}: {
  title: string;
  shortcuts: KeyboardShortcut[];
}) => {
  if (shortcuts.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-black/60 dark:text-white/60 uppercase tracking-wide">
        {title}
      </h3>
      <div className="space-y-1">
        {shortcuts.map((shortcut) => (
          <div
            key={`${shortcut.key}-${shortcut.ctrl}-${shortcut.shift}`}
            className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-light-200/50 dark:hover:bg-dark-200/50 transition-colors"
          >
            <span className="text-sm text-black/80 dark:text-white/80">
              {shortcut.description}
            </span>
            <ShortcutKey shortcut={shortcut} />
          </div>
        ))}
      </div>
    </div>
  );
};

const KeyboardShortcutsHelp = ({ isOpen, onClose }: KeyboardShortcutsHelpProps) => {
  const navigationShortcuts = KEYBOARD_SHORTCUTS.filter(
    (s) => s.category === 'navigation'
  );
  const actionShortcuts = KEYBOARD_SHORTCUTS.filter(
    (s) => s.category === 'actions'
  );
  const sourceShortcuts = KEYBOARD_SHORTCUTS.filter(
    (s) => s.category === 'sources'
  );
  const otherShortcuts = KEYBOARD_SHORTCUTS.filter(
    (s) => s.category === 'other'
  );

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </TransitionChild>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <TransitionChild
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <DialogPanel data-testid="keyboard-shortcuts-modal" className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-light-primary dark:bg-dark-primary border border-light-200 dark:border-dark-200 shadow-xl transition-all">
                <div className="flex items-center justify-between p-4 border-b border-light-200 dark:border-dark-200">
                  <div className="flex items-center gap-2">
                    <Keyboard className="w-5 h-5 text-sky-500" />
                    <DialogTitle className="text-lg font-medium text-black dark:text-white">
                      Keyboard Shortcuts
                    </DialogTitle>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition-colors"
                  >
                    <X className="w-5 h-5 text-black/60 dark:text-white/60" />
                  </button>
                </div>

                <div className="p-4 space-y-6 max-h-[60vh] overflow-y-auto">
                  <ShortcutGroup title="Navigation" shortcuts={navigationShortcuts} />
                  <ShortcutGroup title="Actions" shortcuts={actionShortcuts} />
                  <ShortcutGroup title="Sources (1-9)" shortcuts={sourceShortcuts} />
                  <ShortcutGroup title="Other" shortcuts={otherShortcuts} />
                </div>

                <div className="p-4 border-t border-light-200 dark:border-dark-200 bg-light-secondary/50 dark:bg-dark-secondary/50">
                  <p className="text-xs text-black/50 dark:text-white/50 text-center">
                    Press <kbd className="px-1.5 py-0.5 text-xs bg-light-200 dark:bg-dark-200 rounded">?</kbd> anytime to show this help
                  </p>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default KeyboardShortcutsHelp;
