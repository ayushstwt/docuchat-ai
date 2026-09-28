import enum


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class MessageRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ActivityAction(str, enum.Enum):
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    CONVERSATION_CREATE = "CONVERSATION_CREATE"
    CHAT_MESSAGE = "CHAT_MESSAGE"


class ActivitySubAction(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
