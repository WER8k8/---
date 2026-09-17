# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出口 IP 上游采购适配器。"""

from app.services.egress.provisioner import (
    EgressProvisionerError,
    PurchasedProxy,
    get_egress_provisioner,
)

__all__ = [
    "EgressProvisionerError",
    "PurchasedProxy",
    "get_egress_provisioner",
]
