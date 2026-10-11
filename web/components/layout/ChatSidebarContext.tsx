"use client";

import { createContext, useContext } from "react";

/**
 * Lets the chat page plug its conversation history into the shared product sidebar
 * (one sidebar for navigation + history, like other chat apps) without lifting chat state into the shell.
 */
export type ChatSidebarContextValue = {
  /** Element inside the sidebar where the chat page renders its history (null off the chat route). */
  slot: HTMLElement | null;
  /** Opens the sidebar drawer on small screens. */
  openSidebar: () => void;
  closeSidebar: () => void;
  /** The shell's "New chat" button calls this handler while the chat page is mounted. */
  registerNewChat: (handler: (() => void) | null) => void;
};

export const ChatSidebarContext = createContext<ChatSidebarContextValue | null>(null);

export function useChatSidebar() {
  return useContext(ChatSidebarContext);
}
