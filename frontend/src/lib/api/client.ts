"use server";

import { getServerJwtToken } from "@/actions/auth";
import axios, { type AxiosInstance } from "axios";

const baseConfig = {
  baseURL: process.env.REST_API_URL || process.env.NEXT_PUBLIC_API_URL,
};

export const publicApiClient: AxiosInstance = axios.create(baseConfig);

const authApiClient: AxiosInstance = axios.create(baseConfig);

authApiClient.interceptors.request.use(async (config) => {
  const token = await getServerJwtToken();
  const jwtAccessToken = token?.jwt_access_token;

  if (!jwtAccessToken) {
    return Promise.reject(
      new Error("Missing JWT access token for protected request."),
    );
  }

  config.headers.Authorization = `JWT ${jwtAccessToken}`;
  return config;
});

/** Shared instance; JWT is applied per request via interceptor (no `axios.create` per call). */
export async function getAuthApiClient(): Promise<AxiosInstance> {
  return authApiClient;
}
