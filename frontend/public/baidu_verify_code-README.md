# 百度站长平台验证文件说明

## 验证步骤

1. **访问百度站长平台**
   - 网址: https://ziyuan.baidu.com/
   - 使用百度账号登录

2. **添加网站**
   - 点击"用户中心" -> "站点管理" -> "添加网站"
   - 输入网站地址: `https://youding.com`

3. **选择验证方式**
   - 选择"HTML文件验证"
   - 下载百度提供的验证文件（文件名类似: `baidu_verify_code-xxxxxx.html`）

4. **放置验证文件**
   - 将下载的验证文件复制到此目录: `frontend/public/`
   - 确保文件可通过 `https://youding.com/baidu_verify_code-xxxxxx.html` 访问

5. **完成验证**
   - 在百度站长平台点击"验证"按钮
   - 验证成功后，文件可以保留或删除

## 站点地图提交

验证完成后，提交站点地图：

1. 进入"链接提交" -> "sitemap"
2. 输入站点地图地址: `https://youding.com/sitemap.xml`
3. 点击"提交"

## 主动推送配置

如需启用主动推送功能：

1. 在百度站长平台获取推送接口地址和token
2. 配置环境变量:
   ```env
   BAIDU_PUSH_API=https://data.zz.baidu.com/urls?site=youding.com&token=YOUR_TOKEN
   ```
3. 执行推送脚本:
   ```bash
   python scripts/baidu_push.py
   ```

## 注意事项

- 验证文件必须放在 `frontend/public/` 目录下
- 验证后建议保留文件，避免重新验证
- 确保Nginx配置允许访问 `.html` 文件
- 生产环境部署后再次验证可访问性
