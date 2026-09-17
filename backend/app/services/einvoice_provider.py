# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""全电发票 Provider 适配层 — 诺诺/百望等可插拔；未配置时走人工 mark-issued。"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class EInvoiceIssueRequest:
    application_id: str
    buyer_title: str
    buyer_tax_id: str | None
    buyer_email: str
    amount_cents: int
    invoice_type: str
    seller_name: str
    seller_tax_id: str
    service_category: str
    order_no: str | None = None


@dataclass
class EInvoiceIssueResult:
    success: bool
    provider: str
    invoice_code: str | None = None
    invoice_number: str | None = None
    pdf_url: str | None = None
    message: str = ""
    raw: dict[str, Any] | None = None


class BaseEInvoiceProvider(ABC):
    name: str = "base"
    @abstractmethod
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        ...

    @abstractmethod
    def issue(self, req: EInvoiceIssueRequest) -> EInvoiceIssueResult:
        """issue。

        参数说明：
        :param self: 参数 self
        :param req: 参数 req
        :return: 返回处理结果。
        """
        ...


class ManualEInvoiceProvider(BaseEInvoiceProvider):
    """默认：不调用第三方，财务在税控系统手工开票后登记。"""
    name = "manual"
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return True

    def issue(self, req: EInvoiceIssueRequest) -> EInvoiceIssueResult:
        """issue。

        参数说明：
        :param self: 参数 self
        :param req: 参数 req
        :return: 返回处理结果。
        """
        return EInvoiceIssueResult(
            success=False,
            provider=self.name,
            message="当前为人工开票模式，请在税控系统开具后使用「标记已开票」",
        )


class NuonuoEInvoiceProvider(BaseEInvoiceProvider):
    """诺诺网全电票 — 需配置 NUONUO_* 环境变量。"""
    name = "nuonuo"
    def __init__(self) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.app_key = (os.getenv("NUONUO_APP_KEY") or "").strip()
        self.app_secret = (os.getenv("NUONUO_APP_SECRET") or "").strip()
        self.tax_num = (os.getenv("NUONUO_SELLER_TAX_NUM") or "").strip()
        self.api_base = (os.getenv("NUONUO_API_BASE") or "https://sdk.nuonuo.com/open/v1/services").strip()

    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self.app_key and self.app_secret and self.tax_num)

    def issue(self, req: EInvoiceIssueRequest) -> EInvoiceIssueResult:
        """issue。

        参数说明：
        :param self: 参数 self
        :param req: 参数 req
        :return: 返回处理结果。
        """
        if not self.is_configured():
            return EInvoiceIssueResult(
                success=False,
                provider=self.name,
                message="诺诺未配置（NUONUO_APP_KEY / NUONUO_APP_SECRET / NUONUO_SELLER_TAX_NUM）",
            )
        payload = {
            "orderNo": req.order_no or req.application_id,
            "buyerName": req.buyer_title,
            "buyerTaxNum": req.buyer_tax_id or "",
            "email": req.buyer_email,
            "invoiceAmount": round(req.amount_cents / 100, 2),
            "invoiceType": "1" if req.invoice_type == "vat_special" else "2",
            "goodsName": req.service_category,
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{self.api_base}/invoice/issue",
                    json={"appKey": self.app_key, "appSecret": self.app_secret, "taxNum": self.tax_num, "data": payload},
                )
            if resp.status_code >= 400:
                return EInvoiceIssueResult(
                    success=False,
                    provider=self.name,
                    message=f"诺诺 API HTTP {resp.status_code}",
                    raw={"body": resp.text[:500]},
                )
            data = resp.json()
            if str(data.get("code")) not in ("0", "200", "E0000"):
                return EInvoiceIssueResult(
                    success=False,
                    provider=self.name,
                    message=str(data.get("describe") or data.get("message") or "开票失败"),
                    raw=data,
                )
            result = data.get("result") or data.get("data") or {}
            return EInvoiceIssueResult(
                success=True,
                provider=self.name,
                invoice_code=str(result.get("invoiceCode") or result.get("fpdm") or ""),
                invoice_number=str(result.get("invoiceNum") or result.get("fphm") or ""),
                pdf_url=result.get("pdfUrl"),
                message="诺诺开票成功",
                raw=data,
            )
        except Exception as exc:
            return EInvoiceIssueResult(
                success=False,
                provider=self.name,
                message=f"诺诺调用异常: {exc}",
            )


def get_einvoice_provider() -> BaseEInvoiceProvider:
    """get_einvoice_provider。
    :return: 返回处理结果。
    """
    preferred = (os.getenv("EINVOICE_PROVIDER") or "manual").strip().lower()
    if preferred == "nuonuo":
        p = NuonuoEInvoiceProvider()
        if p.is_configured():
            return p
    return ManualEInvoiceProvider()


def build_issue_request(app_row: dict[str, Any], platform: Any) -> EInvoiceIssueRequest:
    """build_issue_request。

    参数说明：
    :param app_row: 参数 app_row
    :param platform: 参数 platform
    :return: 返回处理结果。
    """
    return EInvoiceIssueRequest(
        application_id=str(app_row.get("id")),
        buyer_title=str(app_row.get("title") or ""),
        buyer_tax_id=app_row.get("tax_id"),
        buyer_email=str(app_row.get("recipient_email") or ""),
        amount_cents=int(app_row.get("amount_cents") or 0),
        invoice_type=str(app_row.get("invoice_type") or "vat_general"),
        seller_name=getattr(platform, "seller_name", "") or "",
        seller_tax_id=getattr(platform, "seller_tax_id", "") or "",
        service_category=getattr(platform, "service_category", "") or "信息技术服务*软件服务费",
        order_no=app_row.get("order_no"),
    )
