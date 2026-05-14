"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";

export function useImportUrls(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (urls: string[]) => endpoints.importUrls(projectId, urls),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tasks(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });
    },
  });
}

export function useGenerateSuggestions(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (articleId: string) => endpoints.generateSuggestions(projectId, articleId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tasks(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles(projectId) });
    },
  });
}

export function useReviewSuggestion(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ suggestionId, action, editedAnchorText }: { suggestionId: string; action: string; editedAnchorText?: string }) =>
      endpoints.reviewSuggestion(suggestionId, { action, edited_anchor_text: editedAnchorText }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.reviewQueue(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.suggestions(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.publishChecklist(projectId) });
    },
  });
}

export function useBatchReview(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ suggestionIds, action }: { suggestionIds: string[]; action: string }) =>
      endpoints.batchReview({ suggestion_ids: suggestionIds, action }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.reviewQueue(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.publishChecklist(projectId) });
    },
  });
}

export function usePublish(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (articleIds: string[]) => endpoints.publish(projectId, articleIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tasks(projectId) });
    },
  });
}
