'use client';

import DeleteChat from '@/components/DeleteChat';
import { formatTimeDifference } from '@/lib/utils';
import {
  BookOpenText,
  ClockIcon,
  FileText,
  Globe2Icon,
  Trash2,
  Check,
  X,
  Pencil,
  CheckSquare,
  Square,
} from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { toast } from 'sonner';

export interface Chat {
  id: string;
  title: string;
  createdAt: string;
  sources: string[];
  files: { fileId: string; name: string }[];
}

const Page = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChats, setSelectedChats] = useState<Set<string>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const editInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchChats = async () => {
      setLoading(true);

      const res = await fetch(`/api/chats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      setChats(data.chats);
      setLoading(false);
    };

    fetchChats();
  }, []);

  // Focus edit input when editing starts
  useEffect(() => {
    if (editingChatId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingChatId]);

  // Toggle selection mode
  const toggleSelectionMode = () => {
    setIsSelectionMode(!isSelectionMode);
    if (isSelectionMode) {
      setSelectedChats(new Set());
    }
  };

  // Toggle chat selection
  const toggleChatSelection = (chatId: string) => {
    const newSelection = new Set(selectedChats);
    if (newSelection.has(chatId)) {
      newSelection.delete(chatId);
    } else {
      newSelection.add(chatId);
    }
    setSelectedChats(newSelection);
  };

  // Select all chats
  const selectAllChats = () => {
    if (selectedChats.size === chats.length) {
      setSelectedChats(new Set());
    } else {
      setSelectedChats(new Set(chats.map((c) => c.id)));
    }
  };

  // Bulk delete selected chats
  const handleBulkDelete = async () => {
    if (selectedChats.size === 0) return;

    const confirmDelete = window.confirm(
      `Are you sure you want to delete ${selectedChats.size} chat${selectedChats.size > 1 ? 's' : ''}?`
    );

    if (!confirmDelete) return;

    setIsDeleting(true);
    const deletePromises = Array.from(selectedChats).map((chatId) =>
      fetch(`/api/chats/${chatId}`, { method: 'DELETE' })
    );

    try {
      await Promise.all(deletePromises);
      setChats(chats.filter((chat) => !selectedChats.has(chat.id)));
      toast.success(`Deleted ${selectedChats.size} chat${selectedChats.size > 1 ? 's' : ''}`);
      setSelectedChats(new Set());
      setIsSelectionMode(false);
    } catch (error) {
      toast.error('Failed to delete some chats');
    } finally {
      setIsDeleting(false);
    }
  };

  // Start editing chat title
  const startEditing = (chat: Chat) => {
    setEditingChatId(chat.id);
    setEditingTitle(chat.title);
  };

  // Save edited title
  const saveTitle = async () => {
    if (!editingChatId || !editingTitle.trim()) {
      setEditingChatId(null);
      return;
    }

    try {
      const res = await fetch(`/api/chats/${editingChatId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editingTitle.trim() }),
      });

      if (res.ok) {
        setChats(
          chats.map((chat) =>
            chat.id === editingChatId
              ? { ...chat, title: editingTitle.trim() }
              : chat
          )
        );
        toast.success('Chat renamed');
      } else {
        toast.error('Failed to rename chat');
      }
    } catch (error) {
      toast.error('Failed to rename chat');
    } finally {
      setEditingChatId(null);
    }
  };

  // Cancel editing
  const cancelEditing = () => {
    setEditingChatId(null);
    setEditingTitle('');
  };

  // Handle key press in edit input
  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveTitle();
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  return (
    <div>
      <div className="flex flex-col pt-10 border-b border-light-200/20 dark:border-dark-200/20 pb-6 px-2">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-3">
          <div className="flex items-center justify-center">
            <BookOpenText size={45} className="mb-2.5" />
            <div className="flex flex-col">
              <h1
                className="text-5xl font-normal p-2 pb-0"
                style={{ fontFamily: 'PP Editorial, serif' }}
              >
                Library
              </h1>
              <div className="px-2 text-sm text-black/60 dark:text-white/60 text-center lg:text-left">
                Past chats, sources, and uploads.
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center lg:justify-end gap-2 text-xs text-black/60 dark:text-white/60">
            {/* Selection mode controls */}
            {isSelectionMode && chats.length > 0 && (
              <>
                <button
                  onClick={selectAllChats}
                  className="inline-flex items-center gap-1 rounded-full border border-black/20 dark:border-white/20 px-2 py-0.5 hover:bg-light-200 dark:hover:bg-dark-200 transition-colors"
                >
                  {selectedChats.size === chats.length ? (
                    <CheckSquare size={14} />
                  ) : (
                    <Square size={14} />
                  )}
                  {selectedChats.size === chats.length ? 'Deselect all' : 'Select all'}
                </button>
                {selectedChats.size > 0 && (
                  <button
                    onClick={handleBulkDelete}
                    disabled={isDeleting}
                    className="inline-flex items-center gap-1 rounded-full border border-red-400/50 text-red-500 px-2 py-0.5 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                  >
                    <Trash2 size={14} />
                    Delete {selectedChats.size}
                  </button>
                )}
              </>
            )}

            {/* Toggle selection mode button */}
            {chats.length > 0 && (
              <button
                onClick={toggleSelectionMode}
                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 transition-colors ${isSelectionMode
                    ? 'border-sky-400/50 text-sky-500 bg-sky-500/10'
                    : 'border-black/20 dark:border-white/20 hover:bg-light-200 dark:hover:bg-dark-200'
                  }`}
              >
                {isSelectionMode ? <X size={14} /> : <CheckSquare size={14} />}
                {isSelectionMode ? 'Cancel' : 'Select'}
              </button>
            )}

            <span className="inline-flex items-center gap-1 rounded-full border border-black/20 dark:border-white/20 px-2 py-0.5">
              <BookOpenText size={14} />
              {loading
                ? 'Loading…'
                : `${chats.length} ${chats.length === 1 ? 'chat' : 'chats'}`}
            </span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-row items-center justify-center min-h-[60vh]">
          <svg
            aria-hidden="true"
            className="w-8 h-8 text-light-200 fill-light-secondary dark:text-[#202020] animate-spin dark:fill-[#ffffff3b]"
            viewBox="0 0 100 101"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M100 50.5908C100.003 78.2051 78.1951 100.003 50.5908 100C22.9765 99.9972 0.997224 78.018 1 50.4037C1.00281 22.7993 22.8108 0.997224 50.4251 1C78.0395 1.00281 100.018 22.8108 100 50.4251ZM9.08164 50.594C9.06312 73.3997 27.7909 92.1272 50.5966 92.1457C73.4023 92.1642 92.1298 73.4365 92.1483 50.6308C92.1669 27.8251 73.4392 9.0973 50.6335 9.07878C27.8278 9.06026 9.10003 27.787 9.08164 50.594Z"
              fill="currentColor"
            />
            <path
              d="M93.9676 39.0409C96.393 38.4037 97.8624 35.9116 96.9801 33.5533C95.1945 28.8227 92.871 24.3692 90.0681 20.348C85.6237 14.1775 79.4473 9.36872 72.0454 6.45794C64.6435 3.54717 56.3134 2.65431 48.3133 3.89319C45.869 4.27179 44.3768 6.77534 45.014 9.20079C45.6512 11.6262 48.1343 13.0956 50.5786 12.717C56.5073 11.8281 62.5542 12.5399 68.0406 14.7911C73.527 17.0422 78.2187 20.7487 81.5841 25.4923C83.7976 28.5886 85.4467 32.059 86.4416 35.7474C87.1273 38.1189 89.5423 39.6781 91.9676 39.0409Z"
              fill="currentFill"
            />
          </svg>
        </div>
      ) : chats.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[70vh] px-2 text-center">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl border border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary">
            <BookOpenText className="text-black/70 dark:text-white/70" />
          </div>
          <p className="mt-2 text-black/70 dark:text-white/70 text-sm">
            No chats found.
          </p>
          <p className="mt-1 text-black/70 dark:text-white/70 text-sm">
            <Link href="/" className="text-sky-400">
              Start a new chat
            </Link>{' '}
            to see it listed here.
          </p>
        </div>
      ) : (
        <div className="pt-6 pb-28 px-2" data-testid="chat-list">
          <div className="rounded-2xl border border-light-200 dark:border-dark-200 overflow-hidden bg-light-primary dark:bg-dark-primary">
            {chats.map((chat, index) => {
              const sourcesLabel =
                chat.sources.length === 0
                  ? null
                  : chat.sources.length <= 2
                    ? chat.sources
                      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
                      .join(', ')
                    : `${chat.sources
                      .slice(0, 2)
                      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
                      .join(', ')} + ${chat.sources.length - 2}`;

              const isSelected = selectedChats.has(chat.id);
              const isEditing = editingChatId === chat.id;

              return (
                <div
                  key={chat.id}
                  data-testid="chat-item"
                  className={`group flex flex-col gap-2 p-4 transition-colors duration-200 ${isSelected
                      ? 'bg-sky-500/10'
                      : 'hover:bg-light-secondary dark:hover:bg-dark-secondary'
                    } ${index !== chats.length - 1
                      ? 'border-b border-light-200 dark:border-dark-200'
                      : ''
                    }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    {/* Selection checkbox */}
                    {isSelectionMode && (
                      <button
                        onClick={() => toggleChatSelection(chat.id)}
                        className="pt-1 shrink-0"
                      >
                        {isSelected ? (
                          <CheckSquare
                            size={18}
                            className="text-sky-500"
                          />
                        ) : (
                          <Square
                            size={18}
                            className="text-black/40 dark:text-white/40 hover:text-black/60 dark:hover:text-white/60"
                          />
                        )}
                      </button>
                    )}

                    {/* Chat title - editable or link */}
                    {isEditing ? (
                      <div className="flex-1 flex items-center gap-2">
                        <input
                          ref={editInputRef}
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={handleEditKeyDown}
                          onBlur={saveTitle}
                          className="flex-1 px-2 py-1 text-base lg:text-lg font-medium bg-light-secondary dark:bg-dark-secondary border border-light-300 dark:border-dark-300 rounded focus:outline-none focus:border-sky-500 text-black dark:text-white"
                        />
                        <button
                          onClick={saveTitle}
                          className="p-1 text-green-500 hover:bg-green-500/10 rounded"
                        >
                          <Check size={16} />
                        </button>
                        <button
                          onClick={cancelEditing}
                          className="p-1 text-red-500 hover:bg-red-500/10 rounded"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ) : (
                      <Link
                        href={`/c/${chat.id}`}
                        className="flex-1 text-black dark:text-white text-base lg:text-lg font-medium leading-snug line-clamp-2 group-hover:text-[#24A0ED] transition duration-200"
                        title={chat.title}
                      >
                        {chat.title}
                      </Link>
                    )}

                    {/* Action buttons */}
                    {!isSelectionMode && !isEditing && (
                      <div className="flex items-center gap-1 pt-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => startEditing(chat)}
                          className="p-1 text-black/50 dark:text-white/50 hover:text-black/80 dark:hover:text-white/80 hover:bg-light-200 dark:hover:bg-dark-200 rounded transition-colors"
                          title="Rename chat"
                        >
                          <Pencil size={14} />
                        </button>
                        <DeleteChat
                          chatId={chat.id}
                          chats={chats}
                          setChats={setChats}
                        />
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-black/70 dark:text-white/70">
                    <span className="inline-flex items-center gap-1 text-xs">
                      <ClockIcon size={14} />
                      {formatTimeDifference(new Date(), chat.createdAt)} Ago
                    </span>

                    {sourcesLabel && (
                      <span className="inline-flex items-center gap-1 text-xs border border-black/20 dark:border-white/20 rounded-full px-2 py-0.5">
                        <Globe2Icon size={14} />
                        {sourcesLabel}
                      </span>
                    )}
                    {chat.files.length > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs border border-black/20 dark:border-white/20 rounded-full px-2 py-0.5">
                        <FileText size={14} />
                        {chat.files.length}{' '}
                        {chat.files.length === 1 ? 'file' : 'files'}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default Page;
