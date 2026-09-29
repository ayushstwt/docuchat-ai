import { apiClient } from "./client";
import { ActivityLog, Page } from "./types";

export interface ListActivityLogsParams {
  page?: number;
  size?: number;
}

export const activityLogsApi = {
  list: async (params?: ListActivityLogsParams): Promise<Page<ActivityLog>> => {
    return (await apiClient.get("/activity-logs", {
      params,
    })) as unknown as Page<ActivityLog>;
  },
};
