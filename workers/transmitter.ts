/**
 * transmitter.ts — 加密传输模块
 *
 * 功能：
 * - AES-256-GCM 加密（Web Crypto API）
 * - HMAC-SHA256 签名（时间戳 + nonce 防重放）
 * - HTTPS POST 到 webhook
 * - 3 次自动重试（指数退避 1s / 3s / 9s）
 * - 幂等性：inquiryId 唯一
 */

export interface TransmitPayload {
  inquiryId: string;
  timestamp: number;
  nonce: string;
  encryptedData: string;
  iv: string;
  signature: string;
  algorithm: string;
}

export interface TransmitResult {
  success: boolean;
  inquiryId: string;
  statusCode: number;
  attempts: number;
  error?: string;
}

// ===== 辅助函数 =====

/**
 * 生成随机 nonce（16 字节 hex）
 */
function generateNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * 将字符串转为 Uint8Array
 */
function strToBytes(str: string): Uint8Array {
  return new TextEncoder().encode(str);
}

/**
 * 将 Uint8Array 转为 hex 字符串
 */
function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * 将 hex 字符串转为 Uint8Array
 */
function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

/**
 * 将 base64 字符串转为 Uint8Array
 */
function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * 将 Uint8Array 转为 base64 字符串
 */
function bytesToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// ===== 加密密钥派生 =====

/**
 * 从 hex 密钥字符串导入 AES-GCM 密钥
 */
async function importAesKey(keyHex: string): Promise<CryptoKey> {
  const keyBytes = hexToBytes(keyHex);
  return await crypto.subtle.importKey(
    'raw',
    keyBytes,
    { name: 'AES-GCM' },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * 从 hex 密钥字符串导入 HMAC 密钥
 */
async function importHmacKey(keyHex: string): Promise<CryptoKey> {
  const keyBytes = hexToBytes(keyHex);
  return await crypto.subtle.importKey(
    'raw',
    keyBytes,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify']
  );
}

// ===== 核心函数 =====

/**
 * 使用 AES-256-GCM 加密数据
 *
 * @param data 要加密的 JSON 可序列化数据
 * @param keyHex 32 字节（64 hex 字符）的 AES 密钥
 * @returns { encryptedBase64, ivHex }
 */
export async function encryptPayload(
  data: Record<string, unknown>,
  keyHex: string
): Promise<{ encryptedBase64: string; ivHex: string }> {
  const json = JSON.stringify(data);
  const dataBytes = strToBytes(json);

  // 生成随机 IV（12 字节推荐用于 GCM）
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const aesKey = await importAesKey(keyHex);

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    aesKey,
    dataBytes
  );

  return {
    encryptedBase64: bytesToBase64(new Uint8Array(encrypted)),
    ivHex: bytesToHex(iv),
  };
}

/**
 * 生成 HMAC-SHA256 签名（时间戳 + nonce + 密文）
 *
 * @param encryptedBase64 AES 加密后的 Base64 数据
 * @param timestamp 当前时间戳（毫秒）
 * @param nonce 随机 nonce（16 字节 hex）
 * @param keyHex HMAC 密钥（hex 字符串）
 * @returns HMAC-SHA256 签名字符串
 */
export async function generateSignature(
  encryptedBase64: string,
  timestamp: number,
  nonce: string,
  keyHex: string
): Promise<string> {
  const hmacKey = await importHmacKey(keyHex);
  const message = `${timestamp}:${nonce}:${encryptedBase64}`;
  const messageBytes = strToBytes(message);

  const signature = await crypto.subtle.sign(
    { name: 'HMAC' },
    hmacKey,
    messageBytes
  );

  return bytesToHex(new Uint8Array(signature));
}

/**
 * 指数退避延迟
 */
function backoffDelay(attempt: number): number {
  // 1s, 3s, 9s
  return Math.pow(3, attempt - 1) * 1000;
}

/**
 * 发送加密载荷到 webhook
 *
 * 重试策略：
 * - 第 1 次失败后等待 1 秒重试
 * - 第 2 次失败后等待 3 秒重试
 * - 第 3 次失败后等待 9 秒重试
 * - 3 次全部失败则返回错误
 *
 * @param payload 完整的传输载荷
 * @param webhookUrl webhook 端点
 * @returns 传输结果
 */
export async function transmitInquiry(
  payload: TransmitPayload,
  webhookUrl: string
): Promise<TransmitResult> {
  const maxAttempts = 3;
  let lastError: string | undefined;
  let lastStatusCode = 0;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      if (attempt > 1) {
        const delay = backoffDelay(attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }

      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Inquiry-Id': payload.inquiryId,
          'X-Timestamp': String(payload.timestamp),
          'X-Nonce': payload.nonce,
          'X-Signature': payload.signature,
          'X-Algorithm': payload.algorithm,
          'User-Agent': 'InternationalCrawler/1.0',
        },
        body: JSON.stringify(payload),
      });

      lastStatusCode = response.status;

      // 2xx 视为成功
      if (response.ok) {
        return {
          success: true,
          inquiryId: payload.inquiryId,
          statusCode: response.status,
          attempts: attempt,
        };
      }

      // 4xx 客户端错误不重试（幂等性问题、认证失败等）
      if (response.status >= 400 && response.status < 500) {
        const body = await response.text().catch(() => '');
        return {
          success: false,
          inquiryId: payload.inquiryId,
          statusCode: response.status,
          attempts: attempt,
          error: `Client error: ${response.status} ${body.substring(0, 200)}`,
        };
      }

      lastError = `Server error: ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
  }

  return {
    success: false,
    inquiryId: payload.inquiryId,
    statusCode: lastStatusCode,
    attempts: maxAttempts,
    error: lastError || 'Max retries exceeded',
  };
}

/**
 * 一键创建并传输加密的询盘数据
 *
 * 便捷函数：组合 encryptPayload + generateSignature + transmitInquiry
 *
 * @param inquiryId 唯一询盘 ID（用于幂等）
 * @param data 要加密传输的数据
 * @param webhookUrl webhook 端点 URL
 * @param aesKeyHex AES-256 密钥（64 hex 字符）
 * @param hmacKeyHex HMAC 密钥（64 hex 字符）
 */
export async function encryptAndTransmit(
  inquiryId: string,
  data: Record<string, unknown>,
  webhookUrl: string,
  aesKeyHex: string,
  hmacKeyHex: string
): Promise<TransmitResult> {
  const timestamp = Date.now();
  const nonce = generateNonce();

  const { encryptedBase64, ivHex } = await encryptPayload(data, aesKeyHex);
  const signature = await generateSignature(encryptedBase64, timestamp, nonce, hmacKeyHex);

  const payload: TransmitPayload = {
    inquiryId,
    timestamp,
    nonce,
    encryptedData: encryptedBase64,
    iv: ivHex,
    signature,
    algorithm: 'AES-256-GCM+HMAC-SHA256',
  };

  return transmitInquiry(payload, webhookUrl);
}
