"use server";

import { revalidatePath } from "next/cache";
import { getAuthApiClient } from "@/lib/auth-api";
import { publicApiClient } from "@/lib/api";
import { isAxiosError } from "axios";

/**
 * Submit a rating for a course
 */
export async function rateCourse(
  courseId: string | number,
  rating: number,
  feedback: string,
) {
  try {
    const client = await getAuthApiClient();
    const response = await client.post(`/api/courses/${courseId}/rate/`, {
      rating,
      feedback,
    });

    if (response.status === 200 || response.status === 201) {
      revalidatePath(`/courses/${courseId}`);
      return {
        success: true,
        message: response.data.detail || "تم حفظ التقييم بنجاح",
      };
    }

    return { success: false, message: "حدث خطأ أثناء حفظ التقييم" };
  } catch (error: unknown) {
    console.error("Error rating course:", error);

    let message = "فشل الاتصال بالخادم";
    if (isAxiosError(error)) {
      message =
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        message;
    }
    return {
      success: false,
      message,
    };
  }
}

/**
 * Submit a rating for an instructor
 */
/** The course the rating is about: a physical course id or an online course uuid. */
export type InstructorRatingCourse =
  | { course: number; online_course?: never }
  | { online_course: string; course?: never };

export async function rateInstructor(
  instructorId: number,
  ratedCourse: InstructorRatingCourse,
  rating: number,
  feedback: string,
) {
  try {
    const client = await getAuthApiClient();
    const response = await client.post(
      `/api/users/instructors/${instructorId}/rate/`,
      {
        ...ratedCourse,
        rating,
        feedback,
      },
    );

    if (response.status === 200 || response.status === 201) {
      revalidatePath(`/instructors/${instructorId}`);
      return {
        success: true,
        message: response.data.detail || "تم حفظ التقييم بنجاح",
      };
    }

    return { success: false, message: "حدث خطأ أثناء حفظ التقييم" };
  } catch (error: unknown) {
    let message = "فشل الاتصال بالخادم";
    if (isAxiosError(error)) {
      message =
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        (typeof error.response?.data === "object" && error.response?.data
          ? (Object.values(error.response.data).flat()[0] as string)
          : null) ||
        message;
    }
    return {
      success: false,
      message,
    };
  }
}

/**
 * Fetch course ratings
 */
export async function getCourseRatings(courseId: string | number) {
  try {
    const response = await publicApiClient.get(
      `/api/courses/${courseId}/ratings/`,
    );
    return { success: true, data: response.data };
  } catch (error: unknown) {
    console.error("Error fetching course ratings:", error);
    return { success: false, message: "فشل تحميل التقييمات" };
  }
}

/**
 * Fetch instructor ratings
 */
export async function getInstructorRatings(instructorId: number) {
  try {
    const response = await publicApiClient.get(
      `/api/users/instructors/${instructorId}/ratings/`,
    );
    return { success: true, data: response.data };
  } catch (error: unknown) {
    console.error("Error fetching instructor ratings:", error);
    return { success: false, message: "فشل تحميل التقييمات" };
  }
}

export async function rateOnlineCourse(courseId: string, rating: number, feedback: string) {
  try {
    const client = await getAuthApiClient();
    const response = await client.post(`/api/online-courses/courses/${courseId}/rate/`, {
      rating,
      feedback,
    });

    if (response.status === 200 || response.status === 201) {
      revalidatePath(`/online-courses/${courseId}`);
      return { success: true, message: response.data.detail || "تم حفظ التقييم بنجاح" };
    }

    return { success: false, message: "حدث خطأ أثناء حفظ التقييم" };
  } catch (error: unknown) {
    console.error("Error rating online course:", error);
    let message = "فشل الاتصال بالخادم";
    if (isAxiosError(error)) {
      message =
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        message;
    }
    return {
      success: false,
      message,
    };
  }
}

/**
 * Fetch online course ratings
 */
export async function getOnlineCourseRatings(courseId: string) {
  try {
    const response = await publicApiClient.get(`/api/online-courses/courses/${courseId}/ratings/`);
    return { success: true, data: response.data };
  } catch (error: unknown) {
    console.error("Error fetching online course ratings:", error);
    return { success: false, message: "فشل تحميل التقييمات" };
  }
}

