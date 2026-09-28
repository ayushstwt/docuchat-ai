from typing import Any
from app.constants.error_codes import ErrorCode


class AppException(Exception):
    def __init__(self, error: ErrorCode, *args: Any):
        self.error = error
        self.args_tuple = args
        self.message = error.format(*args)
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, error: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND, *args: Any):
        super().__init__(error, *args)


class ConflictException(AppException):
    def __init__(self, error: ErrorCode = ErrorCode.EMAIL_ALREADY_EXISTS, *args: Any):
        super().__init__(error, *args)


class UnauthorizedException(AppException):
    def __init__(self, error: ErrorCode = ErrorCode.INVALID_CREDENTIALS, *args: Any):
        super().__init__(error, *args)


class ForbiddenException(AppException):
    def __init__(self, error: ErrorCode = ErrorCode.FORBIDDEN, *args: Any):
        super().__init__(error, *args)


class ServiceException(AppException):
    def __init__(self, error: ErrorCode = ErrorCode.AI_SERVICE_UNAVAILABLE, *args: Any):
        super().__init__(error, *args)
