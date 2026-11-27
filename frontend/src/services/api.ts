const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(${API_BASE_URL}, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(API Error (): );
  }

  return response.json() as Promise<T>;
}

export const systemApi = {
  health: () => apiFetch<{ status: string; service: string; port: number }>('/health'),
};
