"use server";

import { isAxiosError } from "axios";
import {
  apiRequest,
  getApiErrorDetail,
  getAuthApiClient,
  parseApiFieldErrors,
  unwrapPaginated,
} from "@/lib/api";
import type { PaginatedResponse } from "@/types/config";
import type {
  EnrollmentListItem,
  EnrollmentProgress,
  EnrollmentRequestCreateBody,
  EnrollmentRequestListItem,
  InstructorEnrollmentListItem,
} from "@/types/entities";

export interface CreateEnrollmentRequestResult {
  ok: boolean;
  message?: string;
  fieldErrors?: Record<string, string[]>;
}

export async function getMyEnrollmentRequests(): Promise<
  EnrollmentRequestListItem[]
> {
  return apiRequest(
    "Failed to load enrollment requests:",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.get<
        | PaginatedResponse<EnrollmentRequestListItem>
        | EnrollmentRequestListItem[]
      >("/api/enrollment-requests/my-requests/?page_size=100");

      return unwrapPaginated(data);
    },
    [],
  );
}

export async function getMyEnrollments(): Promise<EnrollmentListItem[]> {
  return apiRequest(
    "Failed to load enrollments:",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.get<
        PaginatedResponse<EnrollmentListItem> | EnrollmentListItem[]
      >("/api/enrollments/my-enrollments/?page_size=100");

      return unwrapPaginated(data);
    },
    [],
  );
}

export async function getEnrollmentProgressById(
  enrollmentId: string,
): Promise<EnrollmentProgress | null> {
  return apiRequest(
    "Failed to load enrollment progress:",
    async () => {
      const apiClient = await getAuthApiClient();

      const { data } = await apiClient.get<EnrollmentProgress>(
        `/api/enrollments/${enrollmentId}/progress`,
      );

      return data;
    },
    null,
  );
}

export async function getInstructorEnrollmentsByCourseId(courseId: string) {
  return apiRequest(
    "Failed to get course enrollments: ",
    async () => {
      const apiClient = await getAuthApiClient();
      const { data } = await apiClient.get<
        PaginatedResponse<InstructorEnrollmentListItem>
      >(`/api/instructor/courses/${courseId}/enrollments/?page_size=100`);

      return data.results;
    },
    [],
  );
}

export async function createEnrollmentRequest(
  payload: EnrollmentRequestCreateBody,
): Promise<CreateEnrollmentRequestResult> {
  const unexpectedMessage = "حدث خطأ غير متوقع أثناء إرسال الطلب.";
  const axiosFallbackMessage =
    "تعذر إرسال طلب الإلتحاق. يرجى المحاولة مرة أخرى.";

  return apiRequest<CreateEnrollmentRequestResult>(
    "Failed to create enrollment request:",
    async () => {
      const apiClient = await getAuthApiClient();

      await apiClient.post("/api/enrollment-requests/", payload);

      return {
        ok: true,
        message: "تم إرسال طلب الإلتحاق بنجاح.",
      };
    },
    { ok: false, message: unexpectedMessage },
    (error) => {
      if (isAxiosError(error)) {
        const fieldErrors = parseApiFieldErrors(error);
        return {
          ok: false,
          message:
            getApiErrorDetail(error) ||
            fieldErrors?.course?.[0] ||
            fieldErrors?.online_course?.[0] ||
            fieldErrors?.non_field_errors?.[0] ||
            axiosFallbackMessage,
          fieldErrors,
        };
      }

      return { ok: false, message: unexpectedMessage };
    },
  );
}

export async function deleteEnrollmentRequestById(
  enrollmentRequestId: string,
): Promise<boolean> {
  return apiRequest(
    "Failed to cancel enrollment request: ",
    async () => {
      const apiClient = await getAuthApiClient();

      await apiClient.delete(
        `/api/enrollment-requests/${enrollmentRequestId}/cancel/`,
      );

      return true;
    },
    false,
  );
}
