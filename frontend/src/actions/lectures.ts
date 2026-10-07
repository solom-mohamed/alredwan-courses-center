"use server";

import { apiRequest, getAuthApiClient, unwrapPaginated } from "@/lib/api";
import type { PaginatedResponse, TodaysLecturesResponse } from "@/types/config";
import type { LectureDetail, LectureListItem } from "@/types/entities";
import { revalidatePath } from "next/cache";

export async function getLecturesByCourseId(
  courseId: string,
  details: {
    role: string;
    childId?: string;
  },
  params?: {
    page?: number;
    page_size?: number;
    search?: string;
  },
) {
  if (details.role === "parent" && !details.childId) {
    return [];
  }
  return apiRequest(
    "Failed to get lectures: ",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.get<
        PaginatedResponse<LectureListItem> | LectureListItem[]
      >(
        // instructor: /lectures/ · student: /student/lectures/ · parent: /parent/<child>/lectures/
        `/api/courses/${courseId}/${details.role === "instructor" ? "" : `${details.role}/`}${details.childId ? details.childId + "/" : ""}lectures/`,
        {
          params: {
            page_size: params?.page_size ?? 100,
            ...params,
          },
        },
      );

      return unwrapPaginated(data);
    },
    [],
  );
}

export async function getLectureById(lectureId: string) {
  return apiRequest(
    "Failed to get lecture: ",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.get<LectureDetail>(
        `/api/courses/lectures/${lectureId}/`,
      );

      return data;
    },
    null,
  );
}

export async function getInstructorTodaysLectures() {
  return apiRequest(
    "Failed to get today's lectures: ",
    async () => {
      const apiClient = await getAuthApiClient();
      const { data } = await apiClient.get<TodaysLecturesResponse>(
        "/api/courses/lectures/today/",
      );

      return data;
    },
    null,
  );
}

export async function updateLecture(
  lectureId: number,
  payload: Record<string, any>,
) {
  try {
    const client = await getAuthApiClient();

    const response = await client.patch(
      `/api/courses/lectures/${lectureId}/edit/`,
      payload,
      { headers: { "Content-Type": "application/json" } },
    );

    revalidatePath(`/dashboard/lectures/${lectureId}`);
    revalidatePath("/dashboard/(instructor)/todays-schedule");
    revalidatePath("/dashboard/courses");
    revalidatePath("/dashboard/my-courses");

    return { success: true, data: response.data };
  } catch (error: any) {
    console.error("❌ Lecture Update Error:", error);

    let message = "حدث خطأ أثناء تعديل المحاضرة";

    if (error.response?.data) {
      console.error("📦 Response data:", error.response.data);
      const data = error.response.data;

      if (typeof data === "string") {
        message = data;
      } else if (data.detail) {
        message = data.detail;
      } else if (data.message) {
        message = data.message;
      } else if (data.non_field_errors) {
        message = data.non_field_errors[0];
      } else {
        const firstKey = Object.keys(data)[0];
        if (
          firstKey &&
          Array.isArray(data[firstKey]) &&
          data[firstKey].length > 0
        ) {
          message = data[firstKey][0];
        }
      }
    }

    return { success: false, message };
  }
}
