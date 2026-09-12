export interface Env {
  FEISHU_APP_ID: string;
  FEISHU_APP_SECRET: string;
  FEISHU_VERIFICATION_TOKEN: string;
  FEISHU_API_BASE_URL: string;
  FEISHU_LINGMA_WEBHOOK_URL: string;
}

interface TokenCache {
  access_token: string;
  expire_time: number;
}

interface McpRequest {
  id: string;
  method: string;
  params?: Record<string, unknown>;
}

interface McpResponse {
  id: string;
  result?: Record<string, unknown>;
  error?: {
    code: number;
    message: string;
  };
}

interface ToolDescription {
  name: string;
  description: string;
  parameters: Record<string, {
    type: string;
    description: string;
    required?: boolean;
  }>;
}

const FEISHU_API_BASE = "https://open.feishu.cn/open-apis";
let cachedToken: TokenCache | null = null;

async function getTenantToken(env: Env): Promise<string> {
  const now = Date.now();
  
  if (cachedToken && cachedToken.expire_time > now) {
    return cachedToken.access_token;
  }

  const response = await fetch(`${FEISHU_API_BASE}/auth/v3/tenant_access_token/internal`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      app_id: env.FEISHU_APP_ID,
      app_secret: env.FEISHU_APP_SECRET,
    }),
  });

  const data = await response.json() as {
    code: number;
    msg?: string;
    tenant_access_token: string;
    expire: number;
  };
  
  if (data.code !== 0) {
    throw new Error(`Failed to get token: ${data.msg || "Unknown error"}`);
  }

  cachedToken = {
    access_token: data.tenant_access_token,
    expire_time: now + (data.expire - 60) * 1000,
  };

  return cachedToken.access_token;
}

async function sendTextMessage(env: Env, openId: string, text: string): Promise<Record<string, unknown>> {
  const token = await getTenantToken(env);
  
  const response = await fetch(`${FEISHU_API_BASE}/im/v1/messages?receive_id_type=open_id`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({
      receive_id: openId,
      msg_type: "text",
      content: JSON.stringify({ text }),
    }),
  });

  return await response.json();
}

async function sendCardMessage(env: Env, openId: string, card: Record<string, unknown>): Promise<Record<string, unknown>> {
  const token = await getTenantToken(env);
  
  if (!card.config) {
    card.config = { wide_screen_mode: true };
  }

  const response = await fetch(`${FEISHU_API_BASE}/im/v1/messages?receive_id_type=open_id`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({
      receive_id: openId,
      msg_type: "interactive",
      content: JSON.stringify(card),
    }),
  });

  return await response.json();
}

async function getUserInfo(env: Env, openId: string): Promise<Record<string, unknown>> {
  const token = await getTenantToken(env);
  
  const response = await fetch(`${FEISHU_API_BASE}/im/v1/users/${openId}`, {
    headers: {
      "Authorization": `Bearer ${token}`,
    },
  });

  return await response.json();
}

async function batchGetUserId(env: Env, emails: string[]): Promise<Record<string, unknown>> {
  const token = await getTenantToken(env);
  
  const response = await fetch(`${FEISHU_API_BASE}/im/v1/users/batch_get_id`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ emails }),
  });

  return await response.json();
}

async function sendWebhookMessage(webhookUrl: string, content: string, msgType: string = "text"): Promise<Record<string, unknown>> {
  let body: string;
  if (msgType === "interactive") {
    body = JSON.stringify({
      msg_type: "interactive",
      card: JSON.parse(content),
    });
  } else {
    body = JSON.stringify({
      msg_type: "text",
      content: JSON.stringify({ text: content }),
    });
  }

  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  return await response.json();
}

const tools: ToolDescription[] = [
  {
    name: "send_text_message",
    description: "发送文本消息给飞书用户",
    parameters: {
      open_id: {
        type: "string",
        description: "飞书用户的open_id",
        required: true,
      },
      text: {
        type: "string",
        description: "要发送的文本内容",
        required: true,
      },
    },
  },
  {
    name: "send_card_message",
    description: "发送卡片消息给飞书用户",
    parameters: {
      open_id: {
        type: "string",
        description: "飞书用户的open_id",
        required: true,
      },
      card: {
        type: "object",
        description: "飞书卡片消息内容（JSON格式）",
        required: true,
      },
    },
  },
  {
    name: "get_user_info",
    description: "获取飞书用户信息",
    parameters: {
      open_id: {
        type: "string",
        description: "飞书用户的open_id",
        required: true,
      },
    },
  },
  {
    name: "get_user_id_by_email",
    description: "通过邮箱获取飞书用户ID",
    parameters: {
      email: {
        type: "string",
        description: "用户邮箱地址",
        required: true,
      },
    },
  },
  {
    name: "send_text_by_email",
    description: "通过邮箱发送文本消息",
    parameters: {
      email: {
        type: "string",
        description: "收件人邮箱",
        required: true,
      },
      text: {
        type: "string",
        description: "要发送的文本内容",
        required: true,
      },
    },
  },
  {
    name: "send_lingma_text",
    description: "向灵码飞书群发送文本消息（使用Webhook）",
    parameters: {
      text: {
        type: "string",
        description: "要发送的文本内容",
        required: true,
      },
    },
  },
  {
    name: "send_lingma_card",
    description: "向灵码飞书群发送卡片消息（使用Webhook）",
    parameters: {
      card: {
        type: "object",
        description: "飞书卡片消息内容（JSON格式）",
        required: true,
      },
    },
  },
];

function buildWelcomeCard(userName?: string): Record<string, unknown> {
  return {
    config: { wide_screen_mode: true },
    header: {
      title: { tag: "plain_text", content: `👋 欢迎使用优丁建材助手` },
      template: "green",
    },
    elements: [
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: `你好，${userName || "用户"}！我是优丁建材智能助手，可以为你提供以下服务：`,
        },
      },
      { tag: "hr" },
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: "📋 **可用命令：**\n- `help` - 查看帮助信息\n- `产品查询 [关键词]` - 查询产品信息\n- `询盘列表` - 查看最新询盘\n- `绑定账号` - 绑定系统账号接收通知",
        },
      },
    ],
  };
}

function buildInquiryCard(inquiry: Record<string, unknown>): Record<string, unknown> {
  const statusMap: Record<string, string> = {
    pending: "待处理",
    contacted: "已联系",
    closed: "已关闭",
  };
  
  return {
    config: { wide_screen_mode: true },
    header: {
      title: { tag: "plain_text", content: "📩 新询盘通知" },
      template: "red",
    },
    elements: [
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: `**客户姓名：** ${inquiry.name || "未知"}\n**联系电话：** ${inquiry.phone || "无"}\n**电子邮箱：** ${inquiry.email || "无"}\n**感兴趣产品：** ${inquiry.product || "未指定"}\n**状态：** ${statusMap[inquiry.status as string] || inquiry.status}`,
        },
      },
      { tag: "hr" },
      {
        tag: "div",
        text: {
          tag: "lark_md",
          content: `**咨询内容：**\n${inquiry.message || "无"}`,
        },
      },
      { tag: "hr" },
      {
        tag: "action",
        actions: [
          {
            tag: "button",
            text: { tag: "plain_text", content: "✅ 标为已联系" },
            type: "primary",
            value: { action: "mark_contacted", inquiry_id: inquiry.id },
          },
        ],
      },
    ],
  };
}

async function handleToolCall(env: Env, request: McpRequest): Promise<McpResponse> {
  try {
    const { method, params } = request;

    switch (method) {
      case "list_tools":
        return {
          id: request.id,
          result: { tools },
        };

      case "send_text_message": {
        const { open_id, text } = params as Record<string, string>;
        if (!open_id || !text) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: open_id 和 text" },
          };
        }
        const result = await sendTextMessage(env, open_id, text);
        return { id: request.id, result };
      }

      case "send_card_message": {
        const { open_id, card } = params as Record<string, unknown>;
        if (!open_id || !card) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: open_id 和 card" },
          };
        }
        const result = await sendCardMessage(env, open_id as string, card as Record<string, unknown>);
        return { id: request.id, result };
      }

      case "get_user_info": {
        const { open_id } = params as Record<string, string>;
        if (!open_id) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: open_id" },
          };
        }
        const result = await getUserInfo(env, open_id);
        return { id: request.id, result };
      }

      case "get_user_id_by_email": {
        const { email } = params as Record<string, string>;
        if (!email) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: email" },
          };
        }
        const result = await batchGetUserId(env, [email]);
        return { id: request.id, result };
      }

      case "send_text_by_email": {
        const { email, text } = params as Record<string, string>;
        if (!email || !text) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: email 和 text" },
          };
        }
        const userIdResult = await batchGetUserId(env, [email]) as {
          code: number;
          data?: {
            user_list?: Array<{
              user_id: { open_id: string };
            }>;
          };
        };
        if (userIdResult.code !== 0 || !userIdResult.data?.user_list?.length) {
          return {
            id: request.id,
            error: { code: 404, message: "未找到该邮箱对应的飞书用户" },
          };
        }
        const openId = userIdResult.data.user_list[0].user_id.open_id;
        const result = await sendTextMessage(env, openId, text);
        return { id: request.id, result };
      }

      case "send_welcome": {
        const { open_id, user_name } = params as Record<string, string>;
        if (!open_id) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: open_id" },
          };
        }
        const card = buildWelcomeCard(user_name);
        const result = await sendCardMessage(env, open_id, card);
        return { id: request.id, result };
      }

      case "send_inquiry_notification": {
        const { open_id, inquiry } = params as Record<string, unknown>;
        if (!open_id || !inquiry) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: open_id 和 inquiry" },
          };
        }
        const card = buildInquiryCard(inquiry as Record<string, unknown>);
        const result = await sendCardMessage(env, open_id as string, card);
        return { id: request.id, result };
      }

      case "send_lingma_text": {
        const { text } = params as Record<string, string>;
        if (!text) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: text" },
          };
        }
        if (!env.FEISHU_LINGMA_WEBHOOK_URL) {
          return {
            id: request.id,
            error: { code: 500, message: "灵码Webhook地址未配置" },
          };
        }
        const webhookResult = await sendWebhookMessage(env.FEISHU_LINGMA_WEBHOOK_URL, text, "text");
        return { id: request.id, result: webhookResult };
      }

      case "send_lingma_card": {
        const { card: cardParam } = params as Record<string, unknown>;
        if (!cardParam) {
          return {
            id: request.id,
            error: { code: 400, message: "缺少必要参数: card" },
          };
        }
        if (!env.FEISHU_LINGMA_WEBHOOK_URL) {
          return {
            id: request.id,
            error: { code: 500, message: "灵码Webhook地址未配置" },
          };
        }
        const webhookResult = await sendWebhookMessage(env.FEISHU_LINGMA_WEBHOOK_URL, JSON.stringify(cardParam), "interactive");
        return { id: request.id, result: webhookResult };
      }

      default:
        return {
          id: request.id,
          error: { code: 404, message: `未知方法: ${method}` },
        };
    }
  } catch (error) {
    return {
      id: request.id,
      error: {
        code: 500,
        message: error instanceof Error ? error.message : "服务器内部错误",
      },
    };
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (url.pathname === "/mcp" && request.method === "POST") {
      try {
        const body = await request.json() as McpRequest;
        const response = await handleToolCall(env, body);
        return new Response(JSON.stringify(response), {
          headers: { "Content-Type": "application/json" },
        });
      } catch (error) {
        return new Response(
          JSON.stringify({
            error: { code: 400, message: "无效的请求格式" },
          }),
          {
            status: 400,
            headers: { "Content-Type": "application/json" },
          }
        );
      }
    }

    return new Response("Not Found", { status: 404 });
  },
};
