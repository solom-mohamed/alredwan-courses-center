import { getClientAccessToken } from "./temp";
import { getAuthApiClient } from "@/lib/auth-api";
import { unwrapPaginated } from "@/lib/api";
import { Instructor } from "@/types/entities/instructors";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Fetch detailed instructor profile information.
 */
export async function getInstructorDetail(instructorId: string | number) {
  try {
    const token = await getClientAccessToken();
    const response = await fetch(`${API_BASE_URL}/api/users/instructors/${instructorId}/`, {
      headers: {
        Authorization: `JWT ${token}`,
      },
      next: { revalidate: 60 }, // Cache for 1 minute
    });

    if (!response.ok) {
      if (response.status === 404) return null;
      throw new Error("Failed to fetch instructor detail");
    }

    return await response.json();
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Error fetching instructor detail:", error);
    return null;
  }
}

/**
 * Fetch supervisor schedules for a specific instructor.
 */
export async function getSupervisorSchedules(instructorId: string | number) {
  try {
    const token = await getClientAccessToken();
    const response = await fetch(`${API_BASE_URL}/api/attendance/schedules/?instructor=${instructorId}`, {
      headers: {
        Authorization: `JWT ${token}`,
      },
      next: { revalidate: 60 },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch supervisor schedules");
    }

    const data = await response.json();
    return data.results || data;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Error fetching supervisor schedules:", error);
    return [];
  }
}

/**
 * Fetch instructor attendance history (used for the timetable/recent sessions).
 */
export async function getInstructorAttendanceHistory(instructorId: string | number) {
  try {
    const token = await getClientAccessToken();
    const response = await fetch(`${API_BASE_URL}/api/attendance/instructor/${instructorId}/`, {
      headers: {
        Authorization: `JWT ${token}`,
      },
      next: { revalidate: 60 },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch instructor attendance history");
    }

    const data = await response.json();
    return data.results || data;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Error fetching instructor attendance history:", error);
    return [];
  }
}

/**
 * Fetch list of all instructors.
 */
export async function getInstructors(): Promise<Instructor[]> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get("/api/users/instructors/?page_size=100");
    return unwrapPaginated(data) as Instructor[];
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Error fetching instructors:", error);
    return [];
  }
}
