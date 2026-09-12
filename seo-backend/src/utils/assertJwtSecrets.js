/**
 * 主站统一登录 JWT（MAIN_ADMIN_JWT_SECRET / Python JWT_SECRET_KEY）
 * 与矩阵本机 JWT（JWT_SECRET）必须使用不同密钥。
 *
 * 安全原因（简述）：
 * - 两路校验共用同一对称密钥时，攻击者若诱导服务用「另一套」解析逻辑验证同一 blob，
 *   可能放大实现差异带来的风险；且密钥轮换无法分域进行。
 * - 统一登录 Access Token 与矩阵 Node refresh 必须分密钥，以便独立吊销与审计。
 *
 * 在进程启动时调用；若 MAIN_ADMIN_JWT_SECRET 未配置则跳过（未启用主站联邦校验时）。
 */
function assertJwtSecretsSafeOrThrow() {
  const main = process.env.MAIN_ADMIN_JWT_SECRET;
  const node = process.env.JWT_SECRET;
  if (!main || !node) {
    return;
  }
  const a = String(main).trim();
  const b = String(node).trim();
  if (!a || !b) {
    return;
  }
  if (a === b) {
    const err = new Error(
      [
        '[配置错误] MAIN_ADMIN_JWT_SECRET 与 JWT_SECRET 不得相同。',
        '原因：两密钥必须分域——前者与 Python JWT_SECRET_KEY 对齐，用于校验统一登录签发的 Bearer（含 mid 等声明）；',
        '后者仅用于矩阵本机签发的 refresh / 历史 Node Token。',
        '若相同，无法独立轮换密钥，且可能弱化「主站联邦 JWT」与「矩阵本机 JWT」的边界隔离。',
        '请为 MAIN_ADMIN_JWT_SECRET 单独生成强随机串，并写入 Python 侧 JWT_SECRET_KEY。',
      ].join('')
    );
    err.code = 'E_JWT_SECRET_COLLISION';
    throw err;
  }
}

module.exports = { assertJwtSecretsSafeOrThrow };
