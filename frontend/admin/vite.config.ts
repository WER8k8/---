import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import vueJsx from '@vitejs/plugin-vue-jsx';
import { visualizer } from 'rollup-plugin-visualizer';
import dns from 'node:dns';

// 强制 Node.js DNS 解析使用 IPv4，修复 TRAE / Node 20+ 环境中 Vite 仅监听 IPv6 的问题
dns.setDefaultResultOrder('ipv4first');

import Components from 'unplugin-vue-components/vite';
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers';

const lanHost = (process.env.YOUDING_DEV_LAN_HOST || '').trim();

export default defineConfig(({ mode }) => {
  // 后端代理目标：默认 8000（与启动脚本/生产一致）；本地端口被占时用
  // .env.development.local 的 VITE_PROXY_TARGET 覆盖（如 8600），勿提交该文件。
  // 注意：config 上下文必须显式 loadEnv，process.env 不会自动含 .env 文件变量
  const env = loadEnv(mode, process.cwd(), '');
  const backendTarget = (env.VITE_PROXY_TARGET || process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000').replace(/\/$/, '');
  const backendWsTarget = backendTarget.replace(/^http/, 'ws');
  return ({
  base: '/',
  plugins: [
    vue(),
    vueJsx(),
    Components({
      dts: 'src/components.d.ts',
      resolvers: [
        AntDesignVueResolver({
          importStyle: false,
        }),
      ],
    }),
    ...(mode === 'analyze'
      ? [
          visualizer({
            open: false,
            gzipSize: true,
            brotliSize: true,
          }),
        ]
      : []),
  ],
  resolve: {
    alias: [
      // 注意:alias 数组,长前缀优先匹配(避免覆盖 @ 等)
      { find: /^~\//, replacement: resolve(__dirname, '..') + '/' },  // ~/config/plan-catalog → frontend/config/plan-catalog
      { find: '@', replacement: resolve(__dirname, 'src') + '/' },
      { find: '@marketing', replacement: resolve(__dirname, '../config/platform-marketing-content.ts') },
      { find: '@frontend-config', replacement: resolve(__dirname, '../config') + '/' },
    ],
  },
  server: {
    port: 5174,
    /** host:true + dns.setDefaultResultOrder('ipv4first') 确保同时监听 IPv4 */
    host: true,
    /** 允许手机通过局域网 IP 访问（Vite 5.4+ 默认会拦截非白名单 Host） */
    allowedHosts: true,
    /** 联机测试禁用 HMR：远端设备不需要热更新，且 HMR 重连易导致白屏/进程不稳定 */
    ...(lanHost ? { hmr: false } : {}),
    warmup: {
      clientFiles: [
        './src/main.ts',
        './src/App.vue',
        './src/router/index.ts',
        './src/layout/index.vue',
        './src/stores/auth.ts',
        './src/utils/api.ts',
        './src/views/admin/system/overview.vue',
      ],
    },
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        timeout: 600_000,
        proxyTimeout: 600_000,
        selfHandleResponse: true,
        configure: (proxy) => {
          // 完全手动处理代理响应，修复多个 Set-Cookie 头被合并的问题
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 从 rawHeaders 提取所有 Set-Cookie（Node.js headers 对象会合并同名头）
            const rawSetCookies: string[] = [];
            const otherHeaders: Record<string, string> = {};
            for (let i = 0; i < proxyRes.rawHeaders.length; i += 2) {
              const name = proxyRes.rawHeaders[i].toLowerCase();
              let value = proxyRes.rawHeaders[i + 1];
              // 307/308 的 Location 是后端绝对地址（如 http://127.0.0.1:8600/...），
              // 浏览器跨源跟随会被 CORS 拦死 → 改写为相对路径
              if (name === 'location' && value) {
                value = value.replace(/^https?:\/\/[^/]+/i, '');
              }
              if (name === 'set-cookie') {
                rawSetCookies.push(value);
              } else if (!otherHeaders[name]) {
                otherHeaders[name] = value;
              }
            }
            // 设置普通头
            for (const [name, value] of Object.entries(otherHeaders)) {
              res.setHeader(name, value);
            }
            // 设置所有 Set-Cookie 为数组
            if (rawSetCookies.length > 0) {
              res.setHeader('set-cookie', rawSetCookies);
            }
            res.statusCode = proxyRes.statusCode ?? 502;
            proxyRes.pipe(res);
          });
        },
      },
      '/uploads': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/socket.io': {
        target: backendWsTarget,
        ws: true,
        changeOrigin: true,
      },
      '/ws': {
        target: backendWsTarget,
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2020',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'esbuild',
    cssMinify: 'esbuild',
    cssCodeSplit: true,
    modulePreload: { polyfill: false },
    reportCompressedSize: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/ant-design-vue')) return 'antd';
          if (id.includes('node_modules/@ant-design')) return 'antd-icons';
          if (id.includes('node_modules/vue') || id.includes('node_modules/vue-router') || id.includes('node_modules/pinia')) return 'vue';
          // FIX-TDZ: SFC export-helper（withScopeId 等）是所有 SFC 的公共依赖，
          // 若被 manualChunks 分进业务 chunk，会形成 tenants→client→copilot→tenants
          // 循环并在顶层调用时触发 "Cannot access 'Me' before initialization"。
          // 强制归入 vue chunk（单向被依赖），斩断环。
          // 注意虚拟模块 id 是 "\0plugin-vue:export-helper"（含 \0 前缀），按名称匹配。
          if (id.includes('plugin-vue:export-helper') || id.includes('vue/export-helper')) return 'vue';
          if (id.includes('node_modules/echarts') || id.includes('node_modules/vue-echarts')) return 'echarts';
          if (id.includes('/views/client/copilot.vue')) return 'copilot';
          if (id.includes('/views/client/chuhaiji-app.vue')) return 'chuhaiji-app';
          // FIX-27: 按角色壳拆分路由 chunk，减少首次加载体积
          if (id.includes('/views/admin/') && !id.includes('/views/admin/system/')) return 'admin';
          if (id.includes('/views/admin/system/')) return 'admin-system';
          if (id.includes('/views/client/')) return 'client';
          if (id.includes('/views/agent/')) return 'agent';
          if (id.includes('/views/tenants/')) return 'tenants';
          if (id.includes('node_modules/axios') || id.includes('node_modules/dayjs') || id.includes('node_modules/lodash')) return 'utils';
          if (id.includes('node_modules')) return 'vendor';
        },
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: '[ext]/[name]-[hash].[ext]',
      },
    },
    chunkSizeWarningLimit: 500,
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'ant-design-vue',
      '@ant-design/icons-vue',
      'dayjs',
      'dayjs/plugin/relativeTime',
    ],
  },
  });
});
