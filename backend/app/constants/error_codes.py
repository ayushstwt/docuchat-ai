from enum import Enum


class ErrorCode(Enum):
    RESOURCE_NOT_FOUND = ("E001", 404, "Resource with id %s not found")
    USER_NOT_FOUND = ("E002", 404, "User with id %s not found")
    DOCUMENT_NOT_FOUND = ("E003", 404, "Document with id %s not found")
    CONVERSATION_NOT_FOUND = ("E004", 404, "Conversation with id %s not found")
    VALIDATION_FAILED = ("E005", 400, "Validation failed")
    EMAIL_ALREADY_EXISTS = ("E006", 409, "An account with email '%s' already exists")
    INVALID_CREDENTIALS = ("E007", 401, "Invalid email or password")
    TOKEN_INVALID_OR_EXPIRED = ("E008", 401, "Token is invalid, expired, or malformed")
    FORBIDDEN = ("E009", 403, "You do not have permission to access this resource")
    FILE_NOT_PDF = ("E010", 415, "Only PDF files (.pdf) are supported")
    FILE_TOO_LARGE = ("E011", 413, "File size exceeds the maximum limit of %s MB")
    PDF_NO_TEXT = ("E012", 422, "The uploaded PDF contains no extractable text")
    DOCUMENT_NOT_READY = ("E013", 409, "Document is not ready for chat. Current status: %s")
    AI_SERVICE_UNAVAILABLE = ("E014", 502, "The AI service is temporarily unavailable. Please retry shortly")
    RATE_LIMITED = ("E015", 429, "Rate limit exceeded. Try again in %s seconds")
    INTERNAL_ERROR = ("E999", 500, "An unexpected error occurred. Please try again later")

    def __init__(self, code: str, http_status: int, message_template: str):
        self.code = code
        self.http_status = http_status
        self.message_template = message_template

    def format(self, *args: object) -> str:
        if args:
            try:
                return self.message_template % args
            except Exception:
                return self.message_template
        return self.message_template
