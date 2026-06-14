"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";

export function HistoryScreen() {
  const { conversations, loadConversations, openConversation, deleteConversation, pinConversation, renameConversation } =
    useEchoStore(
      useShallow((s) => ({
        conversations: s.conversations,
        loadConversations: s.loadConversations,
        openConversation: s.openConversation,
        deleteConversation: s.deleteConversation,
        pinConversation: s.pinConversation,
        renameConversation: s.renameConversation,
      })),
    );

  const [search, setSearch] = useState("");
  const [renaming, setRenaming] = useState<{ id: string; title: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConversations().finally(() => setLoading(false));
  }, [loadConversations]);

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.preview.toLowerCase().includes(search.toLowerCase()),
  );

  const sorted = [...filtered].sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  });

  function formatDate(iso: string) {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60 * 1000) return "just now";
    if (diff < 60 * 60 * 1000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString();
  }

  async function handleRename() {
    if (!renaming || !renaming.title.trim()) return;
    await renameConversation(renaming.id, renaming.title.trim());
    setRenaming(null);
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 pt-6 pb-4 border-b border-zinc-900">
        <h1 className="text-xl font-bold text-white mb-4">History</h1>
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search conversations…"
          className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-amber-500 transition-colors"
        />
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {loading && (
          <div className="text-center py-12 text-zinc-600 text-sm">Loading…</div>
        )}

        {!loading && sorted.length === 0 && (
          <div className="text-center py-12">
            <p className="text-zinc-600 text-sm">No conversations yet.</p>
            <p className="text-zinc-700 text-xs mt-1">Start one from the Home tab.</p>
          </div>
        )}

        {sorted.map((conv) => (
          <motion.div
            key={conv.id}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => openConversation(conv.id)}
              className="w-full text-left px-4 py-4"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <p className="text-sm font-semibold text-white truncate flex-1">
                  {conv.is_pinned && <span className="text-amber-400 mr-1.5 text-xs font-bold">·</span>}
                  {conv.title}
                </p>
                <span className="text-xs text-zinc-600 flex-shrink-0">{formatDate(conv.updated_at)}</span>
              </div>
              {conv.preview && (
                <p className="text-xs text-zinc-500 line-clamp-2">{conv.preview}</p>
              )}
              <div className="flex items-center gap-3 mt-2">
                <span className="text-xs text-zinc-700">{conv.message_count} messages</span>
              </div>
            </button>

            {/* Actions */}
            <div className="flex border-t border-zinc-800">
              <button
                onClick={() => pinConversation(conv.id, !conv.is_pinned)}
                className="flex-1 py-2.5 text-xs text-zinc-600 hover:text-amber-400 transition-colors"
              >
                {conv.is_pinned ? "Unpin" : "Pin"}
              </button>
              <div className="w-px bg-zinc-800" />
              <button
                onClick={() => setRenaming({ id: conv.id, title: conv.title })}
                className="flex-1 py-2.5 text-xs text-zinc-600 hover:text-white transition-colors"
              >
                Rename
              </button>
              <div className="w-px bg-zinc-800" />
              <button
                onClick={() => deleteConversation(conv.id)}
                className="flex-1 py-2.5 text-xs text-zinc-600 hover:text-red-400 transition-colors"
              >
                Delete
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Rename modal */}
      {renaming && (
        <div className="absolute inset-0 bg-black/80 flex items-end z-50" onClick={() => setRenaming(null)}>
          <div
            className="w-full bg-zinc-900 rounded-t-3xl px-6 pt-6 pb-8 border-t border-zinc-800"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-white font-semibold mb-4">Rename conversation</h3>
            <input
              value={renaming.title}
              onChange={(e) => setRenaming({ ...renaming, title: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && handleRename()}
              autoFocus
              className="w-full bg-zinc-800 border border-zinc-700 rounded-2xl px-4 py-3 text-white text-sm mb-4 focus:outline-none focus:border-amber-500"
            />
            <button
              onClick={handleRename}
              className="w-full bg-amber-500 text-black font-semibold py-3.5 rounded-2xl text-sm"
            >
              Save
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
