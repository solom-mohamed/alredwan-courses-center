"use server";

import { isAxiosError } from "axios";
import { apiRequest, getAuthApiClient } from "@/lib/api";
import type { PaginatedResponse } from "@/types/config";
import type {
  StaffAttendanceDetail,
  StaffAttendanceListItem,
} from "@/types/entities";

export async function getTodaysAttendances() {
  return apiRequest(
    "Failed to get today's attendance: ",
    async () => {
      const apiClient = await getAuthApiClient();
      const { data } = await apiClient.get<
        PaginatedResponse<StaffAttendanceListItem>
      >("/api/attendance/today/?page_size=1000");

      return data.results;
    },
    [],
  );
}

export async function manualCheckIn(id: number) {
  return apiRequest(
    "Failed to manually check in attendance: ",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.post<StaffAttendanceDetail>(
        `/api/attendance/${id}/manual-check-in/`,
      );

      return data;
    },
    null,
  );
}

export async function manualCheckOut(id: number) {
  return apiRequest(
    "Failed to manually check out attendance: ",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.post<StaffAttendanceDetail>(
        `/api/attendance/${id}/manual-check-out/`,
      );

      return data;
    },
    null,
  );
}

export async function getAttendances(params?: {
  date?: string;
  instructor?: number;
  status?: string;
  attendance_type?: string;
  season?: number;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  try {
    const apiClient = await getAuthApiClient();

    // Map 'date' to 'date_from' and 'date_to' for the backend filter
    const apiParams: Record<string, any> = { page_size: 1000, ...params };
    if (apiParams.date) {
      apiParams.date_from = apiParams.date;
      apiParams.date_to = apiParams.date;
      delete apiParams.date;
    }
    // The API's `instructor` filter takes the user UUID; we hold the Instructor id.
    if (apiParams.instructor) {
      apiParams.instructor_id = apiParams.instructor;
      delete apiParams.instructor;
    }

    const { data } = await apiClient.get<
      PaginatedResponse<StaffAttendanceListItem> | StaffAttendanceListItem[]
    >("/api/attendance/all/", { params: apiParams });

    return Array.isArray(data) ? data : data.results;
  } catch (error: unknown) {
    if (typeof error === "object" && error !== null && "digest" in error) {
      if (error.digest === "DYNAMIC_SERVER_USAGE") throw error;
    }
    const errMssg = "Failed to get attendances: ";

    if (isAxiosError(error)) {
      console.error(errMssg, error.response?.data ?? error.message);
    } else {
      console.error(errMssg, error);
    }

    return [];
  }
}

export async function markAbsent(id: number) {
  try {
    const apiClient = await getAuthApiClient();

    const { data } = await apiClient.post<StaffAttendanceDetail>(
      `/api/attendance/${id}/mark-absent/`,
    );

    return data;
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    const errMssg = "Failed to mark attendance as absent: ";

    if (isAxiosError(error)) {
      console.error(errMssg, error.response?.data ?? error.message);
    } else {
      console.error(errMssg, error);
    }

    return null;
  }
}

export async function rateAttendance(
  id: number,
  rating: number,
  notes?: string,
) {
  try {
    const apiClient = await getAuthApiClient();

    const { data } = await apiClient.post<StaffAttendanceDetail>(
      `/api/attendance/${id}/rate/`,
      { rating, notes },
    );

    return data;
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    const errMssg = "Failed to rate attendance: ";

    if (isAxiosError(error)) {
      console.error(errMssg, error.response?.data ?? error.message);
    } else {
      console.error(errMssg, error);
    }

    return null;
  }
}

export async function generateAttendances(startDate: string, endDate: string) {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.post("/api/attendance/generate/", {
      start_date: startDate,
      end_date: endDate,
    });
    return { success: true, data };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    let message = "Failed to generate attendances";
    if (isAxiosError(error)) {
      message =
        error.response?.data?.error || error.response?.data?.detail || message;
    }
    return { success: false, error: message };
  }
}

export async function getWebSocketTicket(): Promise<string | null> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.post<{ ticket: string }>("/api/attendance/ws-ticket/");
    return data.ticket;
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to fetch websocket ticket:", error);
    return null;
  }
}
