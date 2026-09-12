/**
 * test.js — 本地爬虫测试脚本
 *
 * 在不依赖 Worker runtime 的情况下对爬虫引擎进行端到端测试。
 * 依赖 Node.js 18+ 原生支持的 fetch、Web Crypto API。
 *
 * 运行方式:
 *   node test/test.js
 *   REGION=jp node test/test.js
 *   DEBUG=1 node test/test.js
 */

// -- 模拟 Cloudflare Workers 环境变量 (process.env 优先，次之默认值) ----------
process.env.WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://localhost:9099/webhook';
process.env.ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f';
process.env.HMAC_KEY = process.env.HMAC_KEY || 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef';

// Worker 全局引用 `PROXY_ENDPOINT` 未声明，在 crawler.ts 中是通过检查 typeof 的。
// 本地测试时模拟该行为。
globalThis.PROXY_ENDPOINT = process.env.PROXY_ENDPOINT || '';

// -- 导入待测模块 (ESM) ----------------------------------------------------
import { crawlPage } from '../crawler.ts';
import { extractInquiryInfo } from '../extractor.ts';
import { encryptAndTransmit } from '../transmitter.ts';

// -- 辅助 ------------------------------------------------------------------

/** 简易控制台着色 */
const $ = (s, c) => c ? `\x1b[${c}m${s}\x1b[0m` : s;
const GREEN = 32, YELLOW = 33, CYAN = 36, RED = 31, GRAY = 2;

function pass(msg) { console.log(`  ${$('PASS', GREEN)}  ${msg}`); }
function fail(msg) { console.log(`  ${$('FAIL', RED)}  ${msg}`); }
function info(msg) { console.log(`  ${$('INFO', CYAN)}  ${msg}`); }
function detail(label, val) { console.log(`       ${$(label, GRAY)} ${val}`); }

// -- 测试用例 --------------------------------------------------------------

const TEST_URLS = [
  { url: 'https://example.com',            region: 'auto', desc: 'example.com (known fixture)' },
  { url: 'https://httpbin.org/html',       region: 'en',   desc: 'httpbin HTML fixture' },
];

const REGION = process.env.REGION || '';

async function testCrawl(url, region, desc) {
  console.log(`\n${$('=== 测试爬取', CYAN)} ${$(desc, YELLOW)}`);

  const result = await crawlPage({
    url,
    region: region || 'auto',
    timeout: 15000,
  });

  if (result.success) {
    pass(`HTTP ${result.statusCode} | ${result.responseTimeMs}ms`);
    detail('标题:', result.title);
    detail('语言:', result.detectedLanguage);
    detail('最终 URL:', result.finalUrl);
    detail('HTML 长度:', `${result.html.length} 字节`);
  } else {
    fail(`HTTP ${result.statusCode} | ${result.responseTimeMs}ms`);
    detail('错误:', result.error || '未知');
  }

  return result;
}

function testExtractor(html) {
  console.log(`\n${$('=== 测试信息提取', CYAN)}`);

  const extraction = extractInquiryInfo(html);

  info(`邮箱: ${extraction.emails.length} 个`);
  extraction.emails.slice(0, 3).forEach(e => detail('  ', `${e.email} (置信度: ${e.confidence})`));

  info(`电话: ${extraction.phones.length} 个`);
  extraction.phones.slice(0, 3).forEach(p => detail('  ', `${p.phone} -> ${p.formatted}`));

  info(`表单: ${extraction.formFields.length} 个字段`);
  extraction.formFields.slice(0, 3).forEach(f => detail('  ', `${f.name} (${f.type})`));

  info(`询盘段落: ${extraction.inquiryParagraphs.length} 段`);
  extraction.inquiryParagraphs.slice(0, 2).forEach(p =>
    detail('  ', `[${p.relevance}] ${p.text.substring(0, 80)}...`)
  );

  detail('检测语言:', `${extraction.detectedLanguage} (置信度: ${extraction.languageConfidence})`);
  detail('整体置信度:', extraction.overallConfidence);
  detail('联系区:', extraction.contactSectionFound ? '是' : '否');

  return extraction;
}

async function testTransmitter(inquiryId, data) {
  console.log(`\n${$('=== 测试加密传输', CYAN)}`);

  if (!process.env.WEBHOOK_URL || process.env.WEBHOOK_URL === 'http://localhost:9099/webhook') {
    info('未配置真实 WEBHOOK_URL，跳过传输测试。');
    info('设置环境变量可启用: WEBHOOK_URL=<url> node test/test.js');
    return null;
  }

  try {
    const result = await encryptAndTransmit(
      inquiryId,
      data,
      process.env.WEBHOOK_URL,
      process.env.ENCRYPTION_KEY,
      process.env.HMAC_KEY
    );

    if (result.success) {
      pass(`传输成功 (${result.attempts} 次尝试)`);
    } else {
      fail(`传输失败 HTTP ${result.statusCode} | ${result.error}`);
    }

    return result;
  } catch (err) {
    fail(`传输异常: ${err.message}`);
    return null;
  }
}

// -- 主入口 -----------------------------------------------------------------

async function main() {
  console.log($('═══════════════════════════════════════════════', CYAN));
  console.log($('     Workers 爬虫 — 本地测试套件', CYAN));
  console.log($(`     Node ${process.version}`, GRAY));
  console.log($('═══════════════════════════════════════════════', CYAN));

  let targetUrl = process.env.URL;
  let targetRegion = REGION || 'auto';
  let results = [];

  if (targetUrl) {
    // 单 URL 测试模式: URL=<url> REGION=en node test/test.js
    console.log(`\n${$('▶ 单 URL 模式', YELLOW)}`);
    const r = await testCrawl(targetUrl, targetRegion, targetUrl);
    results.push(r);
  } else {
    // 多 URL 测试模式
    console.log(`\n${$('▶ 批量模式', YELLOW)}`);

    for (const tc of TEST_URLS) {
      const region = REGION || tc.region;
      const r = await testCrawl(tc.url, region, tc.desc);
      results.push(r);
    }
  }

  // 信息提取测试（取最后一次爬取成功的结果）
  const lastSuccess = [...results].reverse().find(r => r.success);
  if (lastSuccess) {
    testExtractor(lastSuccess.html);

    // 传输测试
    const inquiryId = `test_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 6)}`;
    const transmitData = {
      url: lastSuccess.finalUrl,
      title: lastSuccess.title,
      detectedLanguage: lastSuccess.detectedLanguage,
      statusCode: lastSuccess.statusCode,
      responseTimeMs: lastSuccess.responseTimeMs,
    };
    await testTransmitter(inquiryId, transmitData);
  }

  // 汇总
  const passed = results.filter(r => r.success).length;
  const total = results.length;

  console.log(`\n${$('═══════════════════════════════════════════════', CYAN)}`);
  console.log(`  ${total > 0 ? (passed === total ? $('全部通过', GREEN) : $('部分通过', YELLOW)) : $('未执行', RED)}`);
  console.log(`  通过: ${passed} / ${total}`);
  console.log($('═══════════════════════════════════════════════', CYAN));

  process.exit(passed === total ? 0 : 1);
}

main().catch(err => {
  console.error($(`\n未捕获异常: ${err.message}`, RED));
  console.error(err.stack);
  process.exit(1);
});
