import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { ApiFieldError, ApiResponse, TokenResponse } from "./types";

export class ApiError extends Error {
  public httpStatus: number;
  public errorCode?: string;
  public fieldErrors?: ApiFieldError[];

  constructor(
    message: string,
    httpStatus: number,
    errorCode?: string,
    fieldErrors?: ApiFieldError[]
  ) {
    super(message);
    this.name = "ApiError";
    this.httpStatus = httpStatus;
    this.errorCode = errorCode;
    this.fieldErrors = fieldErrors;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach Bearer token from localStorage
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("accessToken");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Token Refresh State to handle concurrent 401 requests with single refresh call
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor: unwrap success envelopes and handle 401 token refresh queue
apiClient.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse<unknown>;
    // If metadata exists (paginated response), return Page<T>
    if (data && data.metadata) {
      return {
        items: data.data,
        metadata: data.metadata,
      } as unknown as typeof response.data;
    }
    // Return unwrapped payload data for standard success responses
    return (data && "data" in data ? data.data : data) as typeof response.data;
  },
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle Network / Connection error
    if (!error.response) {
      return Promise.reject(
        new ApiError(
          "Network error. Please check your internet connection.",
          0
        )
      );
    }

    const { status, data } = error.response;
    const errorCode = data?.errorCode;
    const message = data?.message || error.message || "An unexpected error occurred";
    const fieldErrors = data?.errors;

    // Check for 401 with E008 (token expired/invalid) for automatic single refresh
    if (
      status === 401 &&
      errorCode === "E008" &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("refreshToken");
      if (!refreshToken) {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login";
        return Promise.reject(
          new ApiError("Session expired. Please log in again.", 401, "E008")
        );
      }

      try {
        const refreshResponse = await axios.post<ApiResponse<TokenResponse>>(
          `${API_BASE_URL}/auth/refresh`,
          { refreshToken }
        );
        const newTokens = refreshResponse.data.data;
        localStorage.setItem("accessToken", newTokens.accessToken);
        localStorage.setItem("refreshToken", newTokens.refreshToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`;
        }
        processQueue(null, newTokens.accessToken);
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login";
        return Promise.reject(
          new ApiError("Session expired. Please log in again.", 401, "E008")
        );
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(
      new ApiError(message, status, errorCode, fieldErrors)
    );
  }
);
