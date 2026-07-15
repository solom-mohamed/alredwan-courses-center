"use server";

import { apiRequest, getAuthApiClient, unwrapPaginated } from "@/lib/api";
import { PaginatedResponse } from "@/types/config";
import { isAxiosError } from "axios";
import { EnrollmentListItem, EnrollmentRequestListItem } from "@/types/entities";
import { getCourseById } from "@/actions/courses";
import { getEnrollmentProgressById } from "@/actions/enrollments";
import { revalidatePath } from "next/cache";

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
    const response = await apiClient.post("/api/parents/children/create/", data);
    revalidatePath("/dashboard/my-children");
    return { data: response.data, error: null };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    if (isAxiosError(error)) {
      return {
        data: null,
        error: error.response?.data ?? "حدث خطأ أثناء إضافة الطفل",
      };
    }
    return { data: null, error: "حدث خطأ غير متوقع" };
  }
}

export async function updateChild(id: string, data: {
  first_name: string;
  last_name: string;
  dob: string;
  gender: "boy" | "girl";
}) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.patch(`/api/parents/children/${id}/update/`, data);
    revalidatePath("/dashboard/my-children");
    return { data: response.data, error: null };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    if (isAxiosError(error)) {
      return {
        data: null,
        error: error.response?.data ?? "حدث خطأ أثناء تحديث بيانات الطفل",
      };
    }
    return { data: null, error: "حدث خطأ غير متوقع" };
  }
}

export async function deleteChild(id: string) {
  try {
    const apiClient = await getAuthApiClient();
    await apiClient.delete(`/api/parents/children/${id}/delete/`);
    return { error: null };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    if (isAxiosError(error)) {
      return {
        error: error.response?.data ?? "حدث خطأ أثناء حذف الطفل",
      };
    }
    return { error: "حدث خطأ غير متوقع" };
  }
}

export async function getChildById(id: string): Promise<ParentChildDetail | null> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get<ParentChildDetail>(`/api/parents/children/${id}/`);
    return data;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to fetch child details:", error);
    return null;
  }
}

export async function getChildEnrollments(childId: string): Promise<EnrollmentListItem[]> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get<
      PaginatedResponse<EnrollmentListItem> | EnrollmentListItem[]
    >(`/api/enrollments/my-enrollments/?child=${childId}&page_size=100`);

    const results = Array.isArray(data) ? data : data.results;
    return results;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to load child enrollments:", error);
    return [];
  }
}

export async function getChildEnrollmentRequests(childId: string): Promise<EnrollmentRequestListItem[]> {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get<
      PaginatedResponse<EnrollmentRequestListItem> | EnrollmentRequestListItem[]
    >(`/api/enrollment-requests/my-requests/?child=${childId}&page_size=100`);

    const results = Array.isArray(data) ? data : data.results;
    return results;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to load child enrollment requests:", error);
    return [];
  }
}

export async function getChildCourses(childId: string) {
  try {
    const myEnrollments = await getChildEnrollments(childId);

    const myCoursesInitial = await Promise.all(
      myEnrollments.map((e) => getCourseById(e.course)),
    );
    const myEnrollmentsProgresses = await Promise.all(
      myEnrollments.map((e) => getEnrollmentProgressById(e.id)),
    );

    const myCourses = myCoursesInitial.map((c, i) => ({
      ...c,
      course_progress: myEnrollmentsProgresses[i]?.percentage,
    }));

    return myCourses;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to load child courses:", error);
    return [];
  }
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
export async function getInstructorById(id: string | number) {
  try {
    const apiClient = await getAuthApiClient();
    const { data } = await apiClient.get(`/api/users/instructors/${id}/`);
    return data;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Failed to fetch instructor details:", error);
    return null;
  }
}
