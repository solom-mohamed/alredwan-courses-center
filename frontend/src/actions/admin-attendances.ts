"use server";

import { apiRequest, getAuthApiClient } from "@/lib/api";
import { PaginatedResponse } from "@/types/config";
import { isAxiosError } from "axios";
import {
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
      >("/api/attendance/today/");

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
}) {
  try {
    const apiClient = await getAuthApiClient();
    
    // Map 'date' to 'date_from' and 'date_to' for the backend filter
    const apiParams: any = { ...params };
    if (apiParams.date) {
      apiParams.date_from = apiParams.date;
      apiParams.date_to = apiParams.date;
      delete apiParams.date;
    }

    const { data } = await apiClient.get<
      PaginatedResponse<StaffAttendanceListItem>
    >("/api/attendance/all/", { params: apiParams });

    return data.results;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
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
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
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
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
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
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    let message = "Failed to generate attendances";
    if (isAxiosError(error)) {
      message = error.response?.data?.error || error.response?.data?.detail || message;
    }
    return { success: false, error: message };
  }
}
