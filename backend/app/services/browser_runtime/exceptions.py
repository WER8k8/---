"""Browser Runtime 异常体系。"""


class BrowserRuntimeError(Exception):
    """Browser Runtime 异常基类。"""


class BrowserRuntimeDisabled(BrowserRuntimeError):
    """开关未启用或租户不在白名单（默认降级，不外泄）。"""


class BrowserRuntimeUnavailable(BrowserRuntimeError):
    """依赖未就绪（playwright 未装/Profile 不可写/CDP 不可达）—— 降级不外泄。"""


class BrowserRuntimePolicyDenied(BrowserRuntimeError):
    """Policy 闸门拒绝（域名/动作/输入模式违反红线）。"""


class ProfileIsolationError(BrowserRuntimeError):
    """租户 Profile 隔离失败（路径越界/串号）—— 立即终止，绝不静默。"""
