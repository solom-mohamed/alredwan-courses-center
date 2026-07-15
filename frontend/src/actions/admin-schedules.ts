"use server";

import { getAuthApiClient } from "@/lib/auth-api";
import { unwrapPaginated } from "@/lib/api";
import { isAxiosError } from "axios";

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
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
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
      apiClient.get("/api/courses/?page_size=100", { params }),
      apiClient.get("/api/attendance/schedules/?page_size=100", { params }),
    ]);

    const coursesData = unwrapPaginated(coursesRes.data);
    const supervisorData = unwrapPaginated(supervisorRes.data);

    const schedules: WeeklySchedule[] = [];

    // Process Course Schedules by fetching them individually
    const courseSchedulesPromises = coursesData.map(async (course: any) => {
      try {
        const res = await apiClient.get(`/api/courses/${course.id}/schedules/`);
        return { course, schedules: unwrapPaginated(res.data) };
      } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
        return { course, schedules: [] };
      }
    });

    const coursesWithSchedules = await Promise.all(courseSchedulesPromises);

    coursesWithSchedules.forEach(({ course, schedules: courseSchedules }) => {
      courseSchedules.forEach((s: any) => {
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
    });

    // Process Supervisor Schedules
    supervisorData.forEach((s: any) => {
      schedules.push({
        id: s.id,
        weekday: s.day_of_week,
        weekday_display: ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"][s.day_of_week],
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
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to fetch schedules", error);
    return [];
  }
}

export async function createCourseSchedule(courseId: number, data: { weekday: number, start_time: string, end_time: string }) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.post(`/api/courses/${courseId}/schedules/`, data);
    return { success: true, data: response.data };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to create course schedule", error);
    let message = "فشل في إنشاء موعد الدورة";
    if (isAxiosError(error) && error.response?.data) {
      message = JSON.stringify(error.response.data);
    }
    return { success: false, error: message };
  }
}

export async function createSupervisionSchedule(data: { instructor: number, day_of_week: number, start_time: string, end_time: string }) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.post(`/api/attendance/schedules/`, data);
    return { success: true, data: response.data };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to create supervision schedule", error);
    let message = "فشل في إنشاء فترة الإشراف";
    if (isAxiosError(error) && error.response?.data) {
      message = JSON.stringify(error.response.data);
    }
    return { success: false, error: message };
  }
}

export async function deleteCourseSchedule(courseId: number, scheduleId: number) {
  try {
    const apiClient = await getAuthApiClient();
    await apiClient.delete(`/api/courses/${courseId}/schedules/${scheduleId}/`);
    return { success: true };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to delete course schedule", error);
    return { success: false, error: "فشل في حذف موعد الدورة" };
  }
}

export async function deleteSupervisionSchedule(scheduleId: number) {
  try {
    const apiClient = await getAuthApiClient();
    await apiClient.delete(`/api/attendance/schedules/${scheduleId}/`);
    return { success: true };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to delete supervision schedule", error);
    return { success: false, error: "فشل في حذف فترة الإشراف" };
  }
}
