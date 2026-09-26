"use server";

import { cache } from "react";
import { apiRequest, publicApiClient, unwrapPaginated } from "@/lib/api";
import type { PaginatedResponse } from "@/types/config";
import type {
  LandingPageCourse,
  LandingPageInstructor,
  LandingVideo,
} from "@/types/entities";

export const getLandingPageInstructors = cache(
  async (): Promise<LandingPageInstructor[]> => {
    return apiRequest(
      "Failed to load landing page instructors:",
      async () => {
        const { data } = await publicApiClient.get<
          PaginatedResponse<LandingPageInstructor> | LandingPageInstructor[]
        >("/api/users/landingpageinstructors/?page_size=100");

        return unwrapPaginated(data);
      },
      [],
    );
  },
);

export const getLandingPageCourses = cache(
  async (): Promise<LandingPageCourse[]> => {
    return apiRequest(
      "Failed to load landing page courses:",
      async () => {
        const { data } = await publicApiClient.get<
          PaginatedResponse<LandingPageCourse> | LandingPageCourse[]
        >("/api/courses/landingpagecourses/?page_size=6");

        return unwrapPaginated(data);
      },
      [],
    );
  },
);

export const getLandingVideos = cache(async (): Promise<LandingVideo[]> => {
  return apiRequest(
    "Failed to load landing videos:",
    async () => {
      const { data } = await publicApiClient.get<
        PaginatedResponse<LandingVideo> | LandingVideo[]
      >("/api/landing/videos/");

      return unwrapPaginated(data);
    },
    [],
  );
});
