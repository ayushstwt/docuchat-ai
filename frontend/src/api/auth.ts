import { apiClient } from "./client";
import { TokenResponse, User } from "./types";

export interface RegisterPayload {
  email: string;
  password: string;
  fullName: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  register: async (payload: RegisterPayload): Promise<User> => {
    return (await apiClient.post("/auth/register", payload)) as unknown as User;
  },

  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    return (await apiClient.post("/auth/login", payload)) as unknown as TokenResponse;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    return (await apiClient.post("/auth/refresh", { refreshToken })) as unknown as TokenResponse;
  },

  getMe: async (): Promise<User> => {
    return (await apiClient.get("/auth/me")) as unknown as User;
  },
};
