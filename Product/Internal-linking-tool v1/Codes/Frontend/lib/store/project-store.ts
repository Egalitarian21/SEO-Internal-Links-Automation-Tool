"use client";

import { create } from "zustand";


interface ProjectState {
  selectedSuggestionIds: string[];
  toggleSuggestion: (id: string) => void;
  clearSelection: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  selectedSuggestionIds: [],
  toggleSuggestion: (id) =>
    set((state) => ({
      selectedSuggestionIds: state.selectedSuggestionIds.includes(id)
        ? state.selectedSuggestionIds.filter((item) => item !== id)
        : [...state.selectedSuggestionIds, id],
    })),
  clearSelection: () => set({ selectedSuggestionIds: [] }),
}));
