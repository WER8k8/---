"""统一API响应格式"""
# TODO [P2] 高频 API 可迁移到 orjson (pip install orjson) 提升序列化速度 3-5x（待性能瓶颈确认后实施）

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel
from starlette.responses import JSONResponse

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一API响应模型"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    @classmethod
    def success(
            cls,
            data: T = None,
            message: str = "success",
            **kwargs) -> "APIResponse[T]":
        """success。

        参数说明：
        :param cls: 参数 cls
        :param data: 参数 data
        :param message: 参数 message
        :param **kwargs: 参数 **kwargs
        :return: 返回处理结果。
        """
        return cls(code=0, message=message, data=data, **kwargs)

    @classmethod
    def error(cls, code: int, message: str) -> "APIResponse":
        """error。

        参数说明：
        :param cls: 参数 cls
        :param code: 参数 code
        :param message: 参数 message
        :return: 返回处理结果。
        """
        return cls(code=code, message=message)

    @classmethod
    def paginated(cls, data: T, total: int, page: int,
                  page_size: int) -> "APIResponse[T]":
        """paginated。

        参数说明：
        :param cls: 参数 cls
        :param data: 参数 data
        :param total: 参数 total
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        return cls(
            code=0,
            message="success",
            data=data,
            total=total,
            page=page,
            page_size=page_size)


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = None
    message: str


class ValidationErrorResponse(BaseModel):
    """验证错误响应"""
    code: int = 422
    message: str = "参数验证失败"
    errors: list[ErrorDetail] = []


def success_response(data: Any = None, message: str = "success", **kwargs):
    """快捷成功响应"""
    return APIResponse.success(data, message, **kwargs)


def error_response(code: int, message: str):
    """快捷错误响应（4xx/5xx 返回对应 HTTP 状态码 + body.code，非 4xx/5xx 返回 HTTP 200 兼容旧接口）。"""
    if 400 <= code < 600:
        return error_json_response(code, message)
    return APIResponse.error(code, message)


def http_status_for_api_code(code: int) -> int:
    """业务 code 映射 HTTP 状态（4xx/5xx 与 body.code 一致）。"""
    if 400 <= code < 600:
        return code
    return 400


def error_json_response(code: int, message: str) -> JSONResponse:
    """错误响应：body.code 与 HTTP 状态码对齐（媒体工厂等新接口推荐）。"""
    payload = APIResponse.error(code, message).model_dump()
    return JSONResponse(status_code=http_status_for_api_code(code), content=payload)
