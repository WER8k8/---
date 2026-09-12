var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// .wrangler/tmp/bundle-bY4wpg/checked-fetch.js
var urls = /* @__PURE__ */ new Set();
function checkURL(request, init) {
  const url = request instanceof URL ? request : new URL(
    (typeof request === "string" ? new Request(request, init) : request).url
  );
  if (url.port && url.port !== "443" && url.protocol === "https:") {
    if (!urls.has(url.toString())) {
      urls.add(url.toString());
      console.warn(
        `WARNING: known issue with \`fetch()\` requests to custom HTTPS ports in published Workers:
 - ${url.toString()} - the custom port will be ignored when the Worker is published using the \`wrangler deploy\` command.
`
      );
    }
  }
}
__name(checkURL, "checkURL");
globalThis.fetch = new Proxy(globalThis.fetch, {
  apply(target, thisArg, argArray) {
    const [request, init] = argArray;
    checkURL(request, init);
    return Reflect.apply(target, thisArg, argArray);
  }
});

// .wrangler/tmp/bundle-bY4wpg/strip-cf-connecting-ip-header.js
function stripCfConnectingIPHeader(input, init) {
  const request = new Request(input, init);
  request.headers.delete("CF-Connecting-IP");
  return request;
}
__name(stripCfConnectingIPHeader, "stripCfConnectingIPHeader");
globalThis.fetch = new Proxy(globalThis.fetch, {
  apply(target, thisArg, argArray) {
    return Reflect.apply(target, thisArg, [
      stripCfConnectingIPHeader.apply(null, argArray)
    ]);
  }
});

// src/index.ts
var FEISHU_API_BASE = "https://open.feishu.cn/open-apis";
var cachedToken = null;
async function getTenantToken(env) {
  const now = Date.now();
  if (cachedToken && cachedToken.expire_time > now) {
    return cachedToken.access_token;
  }
  const response = await fetch(`${FEISHU_API_BASE}/auth/v3/tenant_access_token/internal`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      app_id: env.FEISHU_APP_ID,
      app_secret: env.FEISHU_APP_SECRET
    })
  });
  const data = await response.json();
  if (data.code !== 0) {
    throw new Error(`Failed to get token: ${data.msg || "Unknown error"}`);
  }
  cachedToken = {
    access_token: data.tenant_access_token,
    expire_time: now + (data.expire - 60) * 1e3
  };
  return cachedToken.access_token;
}
__name(getTenantToken, "getTenantToken");
async function sendTextMessage(env, openId, text) {
  const token = await getTenantToken(env);
  const response = await fetch(`${FEISHU_API_BASE}/im/v1/messages?receive_id_type=open_id`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({
      receive_id: openId,
      msg_type: "text",
      content: JSON.stringify({ text })
    })
  });
  return await response.json();
}
__name(sendTextMessage, "sendTextMessage");
async function sendCardMessage(env, openId, card) {
  const token = await getTenantToken(env);
  if (!card.config) {
    card.config = { wide_screen_mode: true };
  }
  const response = await fetch(`${FEISHU_API_BASE}/im/v1/messages?receive_id_type=open_id`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({
      receive_id: openId,
      msg_type: "interactive",
      content: JSON.stringify(card)
    })
  });
  return await response.json();
}
__name(sendCardMessage, "sendCardMessage");
async function getUserInfo(env, openId) {
  const token = await getTenantToken(env);
  const response = await fetch(`${FEISHU_API_BASE}/im/v1/users/${openId}`, {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });
  return await response.json();
}
__name(getUserInfo, "getUserInfo");
async function batchGetUserId(env, emails) {
  const token = await getTenantToken(env);
  const response = await fetch(`${FEISHU_API_BASE}/im/v1/users/batch_get_id`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ emails })
  });
  return await response.json();
}
__name(batchGetUserId, "batchGetUserId");
async function sendWebhookMessage(webhookUrl, content, msgType = "text") {
  let body;
  if (msgType === "interactive") {
    body = JSON.stringify({
      msg_type: "interactive",
      card: JSON.parse(content)
    });
  } else {
    body = JSON.stringify({
      msg_type: "text",
      content: JSON.stringify({ text: content })
    });
  }
  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body
  });
  return await response.json();
}
__name(sendWebhookMessage, "sendWebhookMessage");
var tools = [
  {
    name: "send_text_message",
    description: "\u53D1\u9001\u6587\u672C\u6D88\u606F\u7ED9\u98DE\u4E66\u7528\u6237",
    parameters: {
      open_id: {
        type: "string",
        description: "\u98DE\u4E66\u7528\u6237\u7684open_id",
        required: true
      },
      text: {
        type: "string",
        description: "\u8981\u53D1\u9001\u7684\u6587\u672C\u5185\u5BB9",
        required: true
      }
    }
  },
  {
    name: "send_card_message",
    description: "\u53D1\u9001\u5361\u7247\u6D88\u606F\u7ED9\u98DE\u4E66\u7528\u6237",
    parameters: {
      open_id: {
        type: "string",
        description: "\u98DE\u4E66\u7528\u6237\u7684open_id",
        required: true
      },
      card: {
        type: "object",
        description: "\u98DE\u4E66\u5361\u7247\u6D88\u606F\u5185\u5BB9\uFF08JSON\u683C\u5F0F\uFF09",
        required: true
      }
    }
  },
  {
    name: "get_user_info",
    description: "\u83B7\u53D6\u98DE\u4E66\u7528\u6237\u4FE1\u606F",
    parameters: {
      open_id: {
        type: "string",
        description: "\u98DE\u4E66\u7528\u6237\u7684open_id",
        required: true
      }
    }
  },
  {
    name: "get_user_id_by_email",
    description: "\u901A\u8FC7\u90AE\u7BB1\u83B7\u53D6\u98DE\u4E66\u7528\u6237ID",
    parameters: {
      email: {
        type: "string",
        description: "\u7528\u6237\u90AE\u7BB1\u5730\u5740",
        required: true
      }
    }
  },
  {
    name: "send_text_by_email",
    description: "\u901A\u8FC7\u90AE\u7BB1\u53D1\u9001\u6587\u672C\u6D88\u606F",
    parameters: {
      email: {
        type: "string",
        description: "\u6536\u4EF6\u4EBA\u90AE\u7BB1",
        required: true
      },
      text: {
        type: "string",
        description: "\u8981\u53D1\u9001\u7684\u6587\u672C\u5185\u5BB9",
        required: true
      }
    }
  },
  {
    name: "send_lingma_text",
    description: "\u5411\u7075\u7801\u98DE\u4E66\u7FA4\u53D1\u9001\u6587\u672C\u6D88\u606F\uFF08\u4F7F\u7528Webhook\uFF09",
    parameters: {
      text: {
        type: "string",
        description: "\u8981\u53D1\u9001\u7684\u6587\u672C\u5185\u5BB9",
        required: true
      }
    }
  },
  {
    name: "send_lingma_card",
    description: "\u5411\u7075\u7801\u98DE\u4E66\u7FA4\u53D1\u9001\u5361\u7247\u6D88\u606F\uFF08\u4F7F\u7528Webhook\uFF09",
    parameters: {
      card: {
        type: "object",
        description: "\u98DE\u4E66\u5361\u7247\u6D88\u606F\u5185\u5BB9\uFF08JSON\u683C\u5F0F\uFF09",
        required: true
      }
    }
  }
];
function buildWelcomeCard(userName) {
  return {
    config: { wide_screen_mode: true },
    header: {
      title: { tag: "plain_text", content: `\u{1F44B} \u6B22\u8FCE\u4F7F\u7528\u4F18\u4E01\u5EFA\u6750\u52A9\u624B` },
      template: "green"
    },
    elements: [
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: `\u4F60\u597D\uFF0C${userName || "\u7528\u6237"}\uFF01\u6211\u662F\u4F18\u4E01\u5EFA\u6750\u667A\u80FD\u52A9\u624B\uFF0C\u53EF\u4EE5\u4E3A\u4F60\u63D0\u4F9B\u4EE5\u4E0B\u670D\u52A1\uFF1A`
        }
      },
      { tag: "hr" },
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: "\u{1F4CB} **\u53EF\u7528\u547D\u4EE4\uFF1A**\n- `help` - \u67E5\u770B\u5E2E\u52A9\u4FE1\u606F\n- `\u4EA7\u54C1\u67E5\u8BE2 [\u5173\u952E\u8BCD]` - \u67E5\u8BE2\u4EA7\u54C1\u4FE1\u606F\n- `\u8BE2\u76D8\u5217\u8868` - \u67E5\u770B\u6700\u65B0\u8BE2\u76D8\n- `\u7ED1\u5B9A\u8D26\u53F7` - \u7ED1\u5B9A\u7CFB\u7EDF\u8D26\u53F7\u63A5\u6536\u901A\u77E5"
        }
      }
    ]
  };
}
__name(buildWelcomeCard, "buildWelcomeCard");
function buildInquiryCard(inquiry) {
  const statusMap = {
    pending: "\u5F85\u5904\u7406",
    contacted: "\u5DF2\u8054\u7CFB",
    closed: "\u5DF2\u5173\u95ED"
  };
  return {
    config: { wide_screen_mode: true },
    header: {
      title: { tag: "plain_text", content: "\u{1F4E9} \u65B0\u8BE2\u76D8\u901A\u77E5" },
      template: "red"
    },
    elements: [
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: `**\u5BA2\u6237\u59D3\u540D\uFF1A** ${inquiry.name || "\u672A\u77E5"}
**\u8054\u7CFB\u7535\u8BDD\uFF1A** ${inquiry.phone || "\u65E0"}
**\u7535\u5B50\u90AE\u7BB1\uFF1A** ${inquiry.email || "\u65E0"}
**\u611F\u5174\u8DA3\u4EA7\u54C1\uFF1A** ${inquiry.product || "\u672A\u6307\u5B9A"}
**\u72B6\u6001\uFF1A** ${statusMap[inquiry.status] || inquiry.status}`
        }
      },
      { tag: "hr" },
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: `**\u54A8\u8BE2\u5185\u5BB9\uFF1A**
${inquiry.message || "\u65E0"}`
        }
      },
      { tag: "hr" },
      {
        tag: "action",
        actions: [
          {
            tag: "button",
            text: { tag: "plain_text", content: "\u2705 \u6807\u4E3A\u5DF2\u8054\u7CFB" },
            type: "primary",
            value: { action: "mark_contacted", inquiry_id: inquiry.id }
          }
        ]
      }
    ]
  };
}
__name(buildInquiryCard, "buildInquiryCard");
async function handleToolCall(env, request) {
  try {
    const { method, params } = request;
    switch (method) {
      case "list_tools":
        return {
          id: request.id,
          result: { tools }
        };
      case "send_text_message": {
        const { open_id, text } = params;
        if (!open_id || !text) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: open_id \u548C text" }
          };
        }
        const result = await sendTextMessage(env, open_id, text);
        return { id: request.id, result };
      }
      case "send_card_message": {
        const { open_id, card } = params;
        if (!open_id || !card) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: open_id \u548C card" }
          };
        }
        const result = await sendCardMessage(env, open_id, card);
        return { id: request.id, result };
      }
      case "get_user_info": {
        const { open_id } = params;
        if (!open_id) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: open_id" }
          };
        }
        const result = await getUserInfo(env, open_id);
        return { id: request.id, result };
      }
      case "get_user_id_by_email": {
        const { email } = params;
        if (!email) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: email" }
          };
        }
        const result = await batchGetUserId(env, [email]);
        return { id: request.id, result };
      }
      case "send_text_by_email": {
        const { email, text } = params;
        if (!email || !text) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: email \u548C text" }
          };
        }
        const userIdResult = await batchGetUserId(env, [email]);
        if (userIdResult.code !== 0 || !userIdResult.data?.user_list?.length) {
          return {
            id: request.id,
            error: { code: 404, message: "\u672A\u627E\u5230\u8BE5\u90AE\u7BB1\u5BF9\u5E94\u7684\u98DE\u4E66\u7528\u6237" }
          };
        }
        const openId = userIdResult.data.user_list[0].user_id.open_id;
        const result = await sendTextMessage(env, openId, text);
        return { id: request.id, result };
      }
      case "send_welcome": {
        const { open_id, user_name } = params;
        if (!open_id) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: open_id" }
          };
        }
        const card = buildWelcomeCard(user_name);
        const result = await sendCardMessage(env, open_id, card);
        return { id: request.id, result };
      }
      case "send_inquiry_notification": {
        const { open_id, inquiry } = params;
        if (!open_id || !inquiry) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: open_id \u548C inquiry" }
          };
        }
        const card = buildInquiryCard(inquiry);
        const result = await sendCardMessage(env, open_id, card);
        return { id: request.id, result };
      }
      case "send_lingma_text": {
        const { text } = params;
        if (!text) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: text" }
          };
        }
        if (!env.FEISHU_LINGMA_WEBHOOK_URL) {
          return {
            id: request.id,
            error: { code: 500, message: "\u7075\u7801Webhook\u5730\u5740\u672A\u914D\u7F6E" }
          };
        }
        const webhookResult = await sendWebhookMessage(env.FEISHU_LINGMA_WEBHOOK_URL, text, "text");
        return { id: request.id, result: webhookResult };
      }
      case "send_lingma_card": {
        const { card: cardParam } = params;
        if (!cardParam) {
          return {
            id: request.id,
            error: { code: 400, message: "\u7F3A\u5C11\u5FC5\u8981\u53C2\u6570: card" }
          };
        }
        if (!env.FEISHU_LINGMA_WEBHOOK_URL) {
          return {
            id: request.id,
            error: { code: 500, message: "\u7075\u7801Webhook\u5730\u5740\u672A\u914D\u7F6E" }
          };
        }
        const webhookResult = await sendWebhookMessage(env.FEISHU_LINGMA_WEBHOOK_URL, JSON.stringify(cardParam), "interactive");
        return { id: request.id, result: webhookResult };
      }
      default:
        return {
          id: request.id,
          error: { code: 404, message: `\u672A\u77E5\u65B9\u6CD5: ${method}` }
        };
    }
  } catch (error) {
    return {
      id: request.id,
      error: {
        code: 500,
        message: error instanceof Error ? error.message : "\u670D\u52A1\u5668\u5185\u90E8\u9519\u8BEF"
      }
    };
  }
}
__name(handleToolCall, "handleToolCall");
var src_default = {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "Content-Type": "application/json" }
      });
    }
    if (url.pathname === "/mcp" && request.method === "POST") {
      try {
        const body = await request.json();
        const response = await handleToolCall(env, body);
        return new Response(JSON.stringify(response), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (error) {
        return new Response(
          JSON.stringify({
            error: { code: 400, message: "\u65E0\u6548\u7684\u8BF7\u6C42\u683C\u5F0F" }
          }),
          {
            status: 400,
            headers: { "Content-Type": "application/json" }
          }
        );
      }
    }
    return new Response("Not Found", { status: 404 });
  }
};

// node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-bY4wpg/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = src_default;

// node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-bY4wpg/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof __Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
__name(__Facade_ScheduledController__, "__Facade_ScheduledController__");
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = (request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    };
    #dispatcher = (type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    };
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=index.js.map
