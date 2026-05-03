from enum import IntEnum
from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class ErrorCode(IntEnum):
    SUCCESS = 0
    INTERNAL_ERROR = 10001
    VALIDATION_ERROR = 10002
    AUTH_REQUIRED = 10003
    AUTH_INVALID = 10004
    PERMISSION_DENIED = 10005
    RESOURCE_NOT_FOUND = 10006
    RESOURCE_CONFLICT = 10007
    RATE_LIMIT_EXCEEDED = 10008
    EXTERNAL_SERVICE_ERROR = 10009
    DATABASE_ERROR = 10010


ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "操作成功",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
    ErrorCode.VALIDATION_ERROR: "请求参数验证失败",
    ErrorCode.AUTH_REQUIRED: "请先登录",
    ErrorCode.AUTH_INVALID: "认证令牌无效或已过期",
    ErrorCode.PERMISSION_DENIED: "无权执行此操作",
    ErrorCode.RESOURCE_NOT_FOUND: "请求的资源不存在",
    ErrorCode.RESOURCE_CONFLICT: "资源状态冲突",
    ErrorCode.RATE_LIMIT_EXCEEDED: "请求过于频繁，请稍后重试",
    ErrorCode.EXTERNAL_SERVICE_ERROR: "外部服务调用失败",
    ErrorCode.DATABASE_ERROR: "数据库操作异常",
}


class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        message: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "未知错误")
        self.status_code = status_code
        self.data = data
        super().__init__(self.message)


def success_response(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    return {
        "code": ErrorCode.SUCCESS,
        "message": message,
        "data": data,
    }


def error_response(
    code: ErrorCode = ErrorCode.INTERNAL_ERROR,
    message: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "code": code,
        "message": message or ERROR_MESSAGES.get(code, "未知错误"),
        "data": data,
    }


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "AppException: code=%s, message=%s, path=%s",
        exc.code,
        exc.message,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=exc.code, message=exc.message, data=exc.data),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    logger.warning("Validation error: %s, path=%s", errors, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=ERROR_MESSAGES[ErrorCode.VALIDATION_ERROR],
            data={"errors": errors},
        ),
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    logger.warning("Pydantic validation error: %s", errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=ERROR_MESSAGES[ErrorCode.VALIDATION_ERROR],
            data={"errors": errors},
        ),
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error("Database error: %s, path=%s", str(exc), request.url.path, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code=ErrorCode.DATABASE_ERROR,
            message=ERROR_MESSAGES[ErrorCode.DATABASE_ERROR],
        ),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s, path=%s", str(exc), request.url.path, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR],
        ),
    )


def register_exception_handlers(app):
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
