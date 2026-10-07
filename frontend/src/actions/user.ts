"use server";

import { isAxiosError } from "axios";
import { revalidatePath } from "next/cache";
import { getCourseById } from "@/actions/courses";
import { getOnlineCourseById } from "@/actions/online-courses";
import { getEnrollmentProgressById } from "@/actions/enrollments";
import {
  apiRequest,
  getAuthApiClient,
  unwrapPaginated,
  publicApiClient,
} from "@/lib/api";
import type { PaginatedResponse } from "@/types/config";
import { getOnlineCourseProgress } from "@/lib/online-courses";
import type {
  EnrollmentListItem,
  EnrollmentRequestListItem,
  StudentCourseItem,
} from "@/types/entities";
import type { InstructorDetail } from "@/types/entities/instructors";

export interface ParentChildDetail {
  id: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  dob: string;
  age: number;
  gender: "girl" | "boy";
  image: string | null;
  unique_code: string;
  primary_parent_name: string;
  created_at: string;
  updated_at: string;
}

export async function getParentChildren(): Promise<ParentChildDetail[]> {
  return apiRequest(
    "Failed to load parent's children:",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.get<
        PaginatedResponse<ParentChildDetail> | ParentChildDetail[]
      >("/api/parents/children/?page_size=100");

      const childrenList = unwrapPaginated(data);
      return childrenList.sort((a, b) => b.age - a.age);
    },
    [],
  );
}

export async function addChild(data: {
  first_name: string;
  last_name: string;
  dob: string;
  gender: "boy" | "girl";
}) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.post(
      "/api/parents/children/create/",
      data,
    );
    revalidatePath("/dashboard/my-children");
    return { data: response.data, error: null };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    if (isAxiosError(error)) {
      return {
        data: null,
        error: error.response?.data ?? "حدث خطأ أثناء إضافة الطفل",
      };
    }
    return { data: null, error: "حدث خطأ غير متوقع" };
  }
}

export async function updateChild(
  id: string,
  data: {
    first_name: string;
    last_name: string;
    dob: string;
    gender: "boy" | "girl";
  },
) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.patch(
      `/api/parents/children/${id}/update/`,
      data,
    );
    revalidatePath("/dashboard/my-children");
    return { data: response.data, error: null };
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    if (isAxiosError(error)) {
      return {
        data: null,
        error: error.response?.data ?? "حدث خطأ أثناء تحديث بيانات الطفل",
      };
    }
    return { data: null, error: "حدث خطأ غير متوقع" };
  }
}

export async function getChildById(
  id: string,
): Promise<ParentChildDetail | null> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get<ParentChildDetail>(
      `/api/parents/children/${id}/`,
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
    console.error("Failed to fetch child details:", error);
    return null;
  }
}

export async function getChildEnrollments(
  childId: string,
): Promise<EnrollmentListItem[]> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get<
      PaginatedResponse<EnrollmentListItem> | EnrollmentListItem[]
    >(`/api/enrollments/my-enrollments/?child=${childId}&page_size=100`);

    const results = Array.isArray(data) ? data : data.results;
    return results;
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to load child enrollments:", error);
    return [];
  }
}

export async function getChildEnrollmentRequests(
  childId: string,
): Promise<EnrollmentRequestListItem[]> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get<
      PaginatedResponse<EnrollmentRequestListItem> | EnrollmentRequestListItem[]
    >(`/api/enrollment-requests/my-requests/?child=${childId}&page_size=100`);

    const results = Array.isArray(data) ? data : data.results;
    return results;
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "digest" in error &&
      error.digest === "DYNAMIC_SERVER_USAGE"
    ) {
      throw error;
    }
    console.error("Failed to load child enrollment requests:", error);
    return [];
  }
}

export async function getChildCourses(
  childId: string,
): Promise<StudentCourseItem[]> {
  return apiRequest(
    "Failed to load child courses:",
    async () => {
      const myEnrollments = await getChildEnrollments(childId);

      const myCourses = await Promise.all(
        myEnrollments.map(async (e): Promise<StudentCourseItem | null> => {
          if (e.course) {
            const [course, progress] = await Promise.all([
              getCourseById(e.course),
              getEnrollmentProgressById(e.id),
            ]);
            if (!course) return null;

            return {
              ...course,
              type: "physical" as const,
              course_progress: progress?.percentage ?? 0,
            };
          }

          if (e.online_course) {
            // Online progress comes from the child's video watch records,
            // which the course detail already carries when `child` is given.
            const course = await getOnlineCourseById(
              String(e.online_course),
              childId,
            );
            if (!course) return null;

            return {
              ...course,
              type: "online" as const,
              course_progress: getOnlineCourseProgress(course.video_lectures),
            };
          }

          return null;
        }),
      );

      return myCourses.filter((c): c is StudentCourseItem => c !== null);
    },
    [],
  );
}

// export async function getInstructorId(phoneNum: string) {
//   try {
//     const formattedPhoneNum = phoneNum.replaceAll(/\D/g, "");

//     const apiClient = await getAuthApiClient();
//     const { data } = await apiClient.get<PaginatedResponse<Instructor>>(
//       `/api/users/instructors/?user__phone_number1__icontains=${formattedPhoneNum}`,
//     );

//     const instructorId = String(data.results[0].id);

//     return instructorId;
//   } catch (err) {
//     if (isAxiosError(err)) {
//       console.error(
//         "Failed to get the instructor: ",
//         err.response?.data ?? err.message,
//       );
//     } else {
//       console.error("Failed to get today's lectures: ", err);
//     }

//     return null;
//   }
// }
export async function getInstructorById(
  id: string | number,
  publicApi: boolean = false,
): Promise<InstructorDetail | null> {
  try {
    const apiClient = publicApi ? publicApiClient : await getAuthApiClient();
    const { data } = await apiClient.get<InstructorDetail>(
      `/api/users/instructors/${id}/`,
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
    console.error("Failed to fetch instructor details:", error);
    return null;
  }
}
