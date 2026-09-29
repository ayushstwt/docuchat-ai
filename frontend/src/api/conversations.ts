import { apiClient } from "./client";
import { Conversation, Message, Page } from "./types";

export interface CreateConversationPayload {
  documentIds: number[];
  title?: string;
}

export interface UpdateConversationPayload {
  title: string;
}

export interface ListParams {
  page?: number;
  size?: number;
}

export const conversationsApi = {
  create: async (payload: CreateConversationPayload): Promise<Conversation> => {
    return (await apiClient.post("/conversations", payload)) as unknown as Conversation;
  },

  list: async (params?: ListParams): Promise<Page<Conversation>> => {
    return (await apiClient.get("/conversations", {
      params,
    })) as unknown as Page<Conversation>;
  },

  getById: async (id: number): Promise<Conversation> => {
    return (await apiClient.get(`/conversations/${id}`)) as unknown as Conversation;
  },

  rename: async (
    id: number,
    payload: UpdateConversationPayload
  ): Promise<Conversation> => {
    return (await apiClient.patch(
      `/conversations/${id}`,
      payload
    )) as unknown as Conversation;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/conversations/${id}`);
  },

  listMessages: async (
    conversationId: number,
    params?: ListParams
  ): Promise<Page<Message>> => {
    return (await apiClient.get(`/conversations/${conversationId}/messages`, {
      params,
    })) as unknown as Page<Message>;
  },
};
