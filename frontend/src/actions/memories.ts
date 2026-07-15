"use server";

import { apiRequest, getAuthApiClient, unwrapPaginated } from "@/lib/api";
import { PaginatedResponse } from "@/types/config";
import { MemoryListItem, ParticipantSearchResult } from "@/types/entities";
import { revalidatePath } from "next/cache";

export async function getGeneralMemories(page_size = 50): Promise<MemoryListItem[]> {
  return apiRequest(
    "Failed to load general memories:",
    async () => {
      const apiClient = await getAuthApiClient();
      const { data } = await apiClient.get<PaginatedResponse<MemoryListItem> | MemoryListItem[]>(
        `/api/memories/feed/general/?page_size=${page_size}`
      );
      return unwrapPaginated(data);
    },
    [],
  );
}

export async function getPrivateMemories(childId?: string, page_size = 50): Promise<MemoryListItem[]> {
  return apiRequest(
    "Failed to load private memories:",
    async () => {
      const apiClient = await getAuthApiClient();
      const url = childId 
        ? `/api/memories/feed/private/?child_id=${childId}&page_size=${page_size}`
        : `/api/memories/feed/private/?page_size=${page_size}`;
      const { data } = await apiClient.get<PaginatedResponse<MemoryListItem> | MemoryListItem[]>(url);
      return unwrapPaginated(data);
    },
    [],
  );
}

export async function searchParticipants(query: string): Promise<ParticipantSearchResult[]> {
  return apiRequest(
    "Failed to search participants:",
    async () => {
      if (query.length < 2) return [];
      const apiClient = await getAuthApiClient();
      const { data } = await apiClient.get<ParticipantSearchResult[]>(
        `/api/memories/participants/search/?q=${encodeURIComponent(query)}`
      );
      return data;
    },
    [],
  );
}

export async function deleteMemory(id: string): Promise<{ ok: boolean; message?: string }> {
  try {
    const apiClient = await getAuthApiClient();
    await apiClient.delete(`/api/memories/${id}/`);
    revalidatePath("/dashboard/memories");
    return { ok: true, message: "تم حذف الذكرى بنجاح" };
  } catch (error: any) {
    return { ok: false, message: error.response?.data?.detail || "حدث خطأ أثناء حذف الذكرى" };
  }
}

export async function getUploadToken(): Promise<{ ok: boolean; token?: string; message?: string }> {
  try {
    const { getServerJwtToken } = await import("@/actions/auth");
    const token = await getServerJwtToken();
    if (!token?.jwt_access_token) throw new Error("Unauthorized");
    
    return { ok: true, token: token.jwt_access_token };
  } catch (error: any) {
    return { ok: false, message: error.message || "حدث خطأ في المصادقة" };
  }
}
