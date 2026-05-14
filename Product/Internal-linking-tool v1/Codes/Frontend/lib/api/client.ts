import axios from "axios";

import type { ApiResponse } from "@/types/api";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export const apiClient = axios.create({
  baseURL,
  timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ??
      error.response?.data?.message ??
      error.message ??
      "Request failed";

    return Promise.reject(new Error(message));
  },
);

export async function apiGet<T>(path: string, params?: Record<string, unknown>) {
  const response = await apiClient.get<ApiResponse<T>>(path, { params });
  return response.data.data;
}

export async function apiPost<T>(path: string, payload?: unknown) {
  const response = await apiClient.post<ApiResponse<T>>(path, payload);
  return response.data.data;
}

export async function apiPatch<T>(path: string, payload?: unknown) {
  const response = await apiClient.patch<ApiResponse<T>>(path, payload);
  return response.data.data;
}
