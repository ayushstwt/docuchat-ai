export type DocumentStatus = "UPLOADED" | "PROCESSING" | "READY" | "FAILED";
export type MessageRole = "USER" | "ASSISTANT";
export type ActivityAction =
  | "REGISTER"
  | "LOGIN"
  | "LOGOUT"
  | "DOCUMENT_UPLOAD"
  | "DOCUMENT_DELETE"
  | "CONVERSATION_CREATE"
  | "CHAT_MESSAGE";
export type ActivitySubAction = "SUCCESS" | "FAILED";

export interface ApiFieldError {
  field: string | null;
  message: string;
}

export interface PageMetadata {
  currentPage: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
}

export interface ApiResponse<T> {
  status: "success" | "error";
  message: string;
  errorCode?: string;
  data: T;
  metadata?: PageMetadata;
  errors?: ApiFieldError[];
  path?: string;
  timestamp: string;
}

export interface Page<T> {
  items: T[];
  metadata: PageMetadata;
}

// DTOs matching backend camelCase exactly

export interface User {
  id: number;
  email: string;
  fullName: string;
  createdOn: string;
}

export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface Document {
  id: number;
  title: string;
  originalFilename: string;
  fileSize: number;
  pageCount: number | null;
  status: DocumentStatus;
  errorCode: string | null;
  createdOn: string;
  updatedOn: string;
}

export interface Conversation {
  id: number;
  title: string;
  documentIds: number[];
  createdOn: string;
  updatedOn: string;
}

export interface Source {
  index: number;
  documentId: number;
  documentTitle: string;
  pageNumber: number;
  snippet: string;
  score: number;
}

export interface Message {
  id: number;
  role: MessageRole;
  content: string;
  sources?: Source[];
  createdOn: string;
}

export interface ActivityLog {
  id: number;
  action: ActivityAction;
  subAction: ActivitySubAction;
  createdOn: string;
}
