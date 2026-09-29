import { apiClient } from "./client";
import { Document, DocumentStatus, Page } from "./types";

export interface ListDocumentsParams {
  page?: number;
  size?: number;
  status?: DocumentStatus;
}

export const documentsApi = {
  list: async (params?: ListDocumentsParams): Promise<Page<Document>> => {
    return (await apiClient.get("/documents", {
      params,
    })) as unknown as Page<Document>;
  },

  getById: async (id: number): Promise<Document> => {
    return (await apiClient.get(`/documents/${id}`)) as unknown as Document;
  },

  upload: async (
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);

    return (await apiClient.post("/documents", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percent);
        }
      },
    })) as unknown as Document;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/documents/${id}`);
  },

  getFileBlobUrl: async (id: number): Promise<string> => {
    const response = await apiClient.get(`/documents/${id}/file`, {
      responseType: "blob",
    });
    return URL.createObjectURL(response as unknown as Blob);
  },
};
