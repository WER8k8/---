import { chromium, Browser, Page } from 'playwright';

async function openFeishuOpenPlatform() {
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: null
  });
  
  const page = await context.newPage();
  
  try {
    console.log('导航到飞书开放平台...');
    await page.goto('https://open.feishu.cn/', { timeout: 30000 });
    
    await page.waitForLoadState('networkidle');
    
    console.log('检测登录状态...');
    const isLoggedIn = await page.$('button:has-text("控制台")') !== null;
    
    if (!isLoggedIn) {
      console.log('请在浏览器中登录飞书开放平台...');
      await page.waitForSelector('button:has-text("控制台")', { timeout: 120000 });
    }
    
    console.log('导航到凭证页面...');
    await page.goto('https://open.feishu.cn/app', { timeout: 30000 });
    
    await page.waitForLoadState('networkidle');
    
    console.log('等待应用列表加载...');
    try {
      await page.waitForSelector('.app-list-item', { timeout: 15000 });
      
      const apps = await page.$$('.app-list-item');
      if (apps.length > 0) {
        console.log(`找到 ${apps.length} 个应用，点击第一个...`);
        await apps[0].click();
        await page.waitForLoadState('networkidle');
        
        console.log('导航到凭证与基础信息...');
        await page.click('text=凭证与基础信息');
        await page.waitForLoadState('networkidle');
      }
    } catch {
      console.log('应用列表未找到，可能需要手动选择');
    }
    
    console.log('提示用户复制凭证...');
    await page.evaluate(() => {
      alert('请复制以下凭证信息：\n\n1. App ID\n2. App Secret\n3. Verification Token（在安全设置中）\n\n复制完成后关闭此弹窗继续');
    });
    
    return browser;
    
  } catch (error) {
    console.error('飞书平台操作失败:', error);
    throw error;
  }
}

async function openCloudflareDashboard() {
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: null
  });
  
  const page = await context.newPage();
  
  try {
    console.log('导航到Cloudflare控制台...');
    await page.goto('https://dash.cloudflare.com/', { timeout: 30000 });
    
    await page.waitForLoadState('networkidle');
    
    console.log('检测登录状态...');
    const isLoggedIn = await page.$('button[data-testid="profile-menu-button"]') !== null;
    
    if (!isLoggedIn) {
      console.log('请在浏览器中登录Cloudflare...');
      await page.waitForSelector('button[data-testid="profile-menu-button"]', { timeout: 120000 });
    }
    
    console.log('导航到API令牌页面...');
    await page.goto('https://dash.cloudflare.com/profile/api-tokens', { timeout: 30000 });
    
    await page.waitForLoadState('networkidle');
    
    console.log('提示用户创建/复制API令牌...');
    await page.evaluate(() => {
      alert('请：\n\n1. 创建一个新的API令牌（选择Workers模板）\n2. 复制API令牌\n3. 复制Account ID（页面右下角）\n\n完成后关闭此弹窗');
    });
    
    return browser;
    
  } catch (error) {
    console.error('Cloudflare操作失败:', error);
    throw error;
  }
}

async function main() {
  console.log('=========================================');
  console.log('  飞书MCP配置凭证获取工具');
  console.log('=========================================');
  console.log('');
  
  let browser: Browser | null = null;
  
  try {
    console.log('[1/2] 正在打开飞书开放平台...');
    browser = await openFeishuOpenPlatform();
    
    console.log('');
    console.log('[2/2] 正在打开Cloudflare控制台...');
    await openCloudflareDashboard();
    
    console.log('');
    console.log('=========================================');
    console.log('  凭证获取完成！');
    console.log('=========================================');
    console.log('');
    console.log('请运行以下命令完成部署：');
    console.log('cd backend/feishu-mcp');
    console.log('.\\deploy.ps1');
    
  } finally {
    if (browser) {
      // 保持浏览器打开供用户操作
    }
  }
}

main().catch(console.error);
