"use server";

import { getAuthApiClient } from "@/lib/auth-api";
import { revalidatePath } from "next/cache";
import { isAxiosError } from "axios";
import { getServerJwtToken } from "@/actions/auth";

export async function updateProfile(data: {
  first_name: string;
  last_name: string;
  email?: string;
  dob: string;
  address?: string;
}) {
  try {
    const apiClient = await getAuthApiClient();
    const response = await apiClient.patch("/auth/users/me/", data);
    revalidatePath("/dashboard/profile");
    return { data: response.data, error: null };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    if (isAxiosError(error)) {
      return {
        data: null,
        error: error.response?.data ?? "حدث خطأ أثناء تحديث الملف الشخصي",
      };
    }
    return { data: null, error: "حدث خطأ غير متوقع" };
  }
}

export async function getMe() {
  try {
    const token = await getServerJwtToken();
    if (!token?.jwt_access_token) return null;

    const response = await fetch(`${process.env.REST_API_URL}/auth/users/me/`, {
      headers: {
        Authorization: `JWT ${token.jwt_access_token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error("getMe failed:", response.status, await response.text());
      return null;
    }

    const data = await response.json();
    return data;
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Error fetching user profile:", error);
    return null;
  }
}

export async function uploadProfileImage(formData: FormData) {
  try {
    const token = await getServerJwtToken();
    if (!token?.jwt_access_token) return { data: null, error: "Authentication required" };

    const response = await fetch(`${process.env.REST_API_URL}/auth/users/me/`, {
      method: "PATCH",
      headers: {
        Authorization: `JWT ${token.jwt_access_token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error("Upload failed:", response.status, errorData);
      return { data: null, error: "حدث خطأ أثناء رفع الصورة" };
    }

    const data = await response.json();
    revalidatePath("/dashboard/profile");
    revalidatePath("/");
    return { data: data, error: null };
  } catch (error: any) {
    if (error?.digest === 'DYNAMIC_SERVER_USAGE') throw error;
    console.error("Upload error:", error);
    return { data: null, error: "حدث خطأ أثناء رفع الصورة" };
  }
}
