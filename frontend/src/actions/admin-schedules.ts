"use server";

import { isAxiosError } from "axios";
import { unwrapPaginated } from "@/lib/api";
import { getAuthApiClient } from "@/lib/auth-api";
import type { CourseListItem, CourseScheduleDetail } from "@/types/entities/courses";
import type { SupervisorSchedule } from "@/types/entities/schedules";

function getErrorMessage(error: unknown, fallback: string): string {
  if (!isAxiosError(error)) {
    return fallback;
  }

  const data = error.response?.data;
  if (!data) {
    return fallback;
  }

  // If data is a string (e.g. Django debug traceback or raw HTML)
  if (typeof data === "string") {
    const trimmed = data.trim();
    if (trimmed.startsWith("<!DOCTYPE") || trimmed.includes("traceback") || trimmed.includes("wsgi")) {
      return fallback;
    }
    return trimmed;
  }

  // If data is an object
  if (typeof data === "object") {
    // 1. Check for 'detail' key
    if ("detail" in data && typeof data.detail === "string") {
      return data.detail;
    }

    // 2. Check for 'non_field_errors' or other array messages
    if ("non_field_errors" in data && Array.isArray(data.non_field_errors)) {
      return data.non_field_errors.join(", ");
    }

    // 3. Fallback to extracting validation error values
    const values = Object.values(data);
    if (values.length > 0) {
      const firstVal = values[0];
      if (Array.isArray(firstVal)) {
        return firstVal.join(", ");
      }
      if (typeof firstVal === "string") {
        return firstVal;
      }
    }
  }

  return fallback;
}

export interface Season {
  id: number;
  name: string;
  is_active: boolean;
}

export interface WeeklySchedule {
  id: number;
  weekday: number;
  weekday_display: string;
  start_time: string;
  end_time: string;
  instructor_name?: string;
  course_name?: string;
  season_name?: string;
  student_count?: number;
  type: "lecture" | "supervision";
}

export async function getSeasons() {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get<Season[]>("/api/courses/seasons/");
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
    if (isAxiosError(error) && error.response?.status === 404) {
      // Endpoint might not exist yet, return empty array gracefully
      return [];
    }
    console.error("Failed to fetch seasons", error);
    return [];
  }
}

export async function getAllSchedules(params?: {
  season?: number;
  instructor?: number;
  weekday?: number;
}) {
  try {
    const apiClient = await getAuthApiClient();

    // We fetch courses and supervisor schedules
    const [coursesRes, supervisorRes] = await Promise.all([
      apiClient.get("/api/courses/?page_size=1000", { params }),
      apiClient.get("/api/attendance/schedules/?page_size=1000", { params }),
    ]);

    const coursesData = unwrapPaginated<CourseListItem>(coursesRes.data);
    const supervisorData = unwrapPaginated<SupervisorSchedule>(supervisorRes.data);

    const schedules: WeeklySchedule[] = [];

    // Process Course Schedules via bulk batch endpoint
    const courseMap = new Map<number, CourseListItem>();
    coursesData.forEach((course) => {
      courseMap.set(course.id, course);
    });

    const courseIds = coursesData.map((c) => c.id);
    let batchSchedules: CourseScheduleDetail[] = [];
    if (courseIds.length > 0) {
      try {
        const schedulesRes = await apiClient.get("/api/courses/schedules/", {
          params: { course_ids: courseIds.join(",") },
        });
        batchSchedules = unwrapPaginated<CourseScheduleDetail>(schedulesRes.data);
      } catch (error: unknown) {
        if (
          error &&
          typeof error === "object" &&
          "digest" in error &&
          error.digest === "DYNAMIC_SERVER_USAGE"
        ) {
          throw error;
        }
        batchSchedules = [];
      }
    }

    batchSchedules.forEach((s: CourseScheduleDetail) => {
      const course = s.course ? courseMap.get(s.course) : undefined;
      if (!course) return;

      const instructorName = course.instructor?.name || "غير محدد";

      schedules.push({
        id: s.id,
        weekday: s.weekday,
        weekday_display: s.weekday_display,
        start_time: s.start_time,
        end_time: s.end_time,
        instructor_name: instructorName,
        course_name: course.name,
        season_name: course.season?.name || "-",
        student_count: course.enrolled_count || 0,
        type: "lecture",
      });
    });

    // Process Supervisor Schedules
    supervisorData.forEach((s: SupervisorSchedule) => {
      schedules.push({
        id: s.id,
        weekday: s.day_of_week,
        // Backend Weekday enum: Saturday=0 … Friday=6.
        weekday_display: [
          "السبت",
          "الأحد",
          "الاثنين",
          "الثلاثاء",
          "الأربعاء",
          "الخميس",
          "الجمعة",
        ][s.day_of_week],
        start_time: s.start_time,
        end_time: s.end_time,
        instructor_name: s.instructor_name,
        course_name: "إشراف",
        season_name: "-",
        student_count: 0,
        type: "supervision",
      });
    });

    return schedules;
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to fetch schedules", error);
    return [];
  }
}

export async function createCourseSchedule(
  courseId: number,
  data: { weekday: number; start_time: string; end_time: string },
) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.post(
      `/api/courses/${courseId}/schedules/`,
      data,
    );
    return { success: true, data: response.data };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to create course schedule", error);
    const message = getErrorMessage(error, "فشل في إنشاء موعد الدورة");
    return { success: false, error: message };
  }
}

export async function createSupervisionSchedule(data: {
  instructor: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  grace_period_minutes?: number;
  auto_absent_after_minutes?: number;
}) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.post(`/api/attendance/schedules/`, data);
    return { success: true, data: response.data };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to create supervision schedule", error);
    const message = getErrorMessage(error, "فشل في إنشاء فترة الإشراف");
    return { success: false, error: message };
  }
}

export async function deleteCourseSchedule(
  courseId: number,
  scheduleId: number,
) {
  try {
    const apiClient = await getAuthApiClient();
    await apiClient.delete(`/api/courses/${courseId}/schedules/${scheduleId}/`);
    return { success: true };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to delete course schedule", error);
    return { success: false, error: "فشل في حذف موعد الدورة" };
  }
}

export async function deleteSupervisionSchedule(scheduleId: number) {
  try {
    const apiClient = await getAuthApiClient();
    await apiClient.delete(`/api/attendance/schedules/${scheduleId}/`);
    return { success: true };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to delete supervision schedule", error);
    return { success: false, error: "فشل في حذف فترة الإشراف" };
  }
}

export async function getOnlySupervisorSchedules(params?: { instructor?: number; day_of_week?: number }) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.get("/api/attendance/schedules/?page_size=1000", { params });
    return unwrapPaginated<SupervisorSchedule>(response.data);
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to fetch supervisor schedules", error);
    return [];
  }
}

export async function updateSupervisionSchedule(
  scheduleId: number,
  data: {
    instructor: number;
    day_of_week: number;
    start_time: string;
    end_time: string;
    grace_period_minutes?: number;
    auto_absent_after_minutes?: number;
  }
) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.patch(`/api/attendance/schedules/${scheduleId}/`, data);
    return { success: true, data: response.data };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to update supervision schedule", error);
    const message = getErrorMessage(error, "فشل في تعديل فترة الإشراف");
    return { success: false, error: message };
  }
}
