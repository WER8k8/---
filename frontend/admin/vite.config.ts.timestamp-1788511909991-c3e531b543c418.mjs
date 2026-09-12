// vite.config.ts
import { defineConfig } from "file:///C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99%E5%BC%80%E5%8F%91%E5%AE%8C%E6%88%90/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99.worktrees/agents-install-vscode-cline-deploy-strix/frontend/admin/node_modules/vite/dist/node/index.js";
import vue from "file:///C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99%E5%BC%80%E5%8F%91%E5%AE%8C%E6%88%90/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99.worktrees/agents-install-vscode-cline-deploy-strix/frontend/admin/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { resolve } from "path";
import vueJsx from "file:///C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99%E5%BC%80%E5%8F%91%E5%AE%8C%E6%88%90/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99.worktrees/agents-install-vscode-cline-deploy-strix/frontend/admin/node_modules/@vitejs/plugin-vue-jsx/dist/index.mjs";
import { visualizer } from "file:///C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99%E5%BC%80%E5%8F%91%E5%AE%8C%E6%88%90/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99.worktrees/agents-install-vscode-cline-deploy-strix/frontend/admin/node_modules/rollup-plugin-visualizer/dist/plugin/index.js";
import dns from "node:dns";
import Components from "file:///C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99%E5%BC%80%E5%8F%91%E5%AE%8C%E6%88%90/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99.worktrees/agents-install-vscode-cline-deploy-strix/frontend/admin/node_modules/unplugin-vue-components/dist/vite.js";
import { AntDesignVueResolver } from "file:///C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99%E5%BC%80%E5%8F%91%E5%AE%8C%E6%88%90/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99.worktrees/agents-install-vscode-cline-deploy-strix/frontend/admin/node_modules/unplugin-vue-components/dist/resolvers.js";
var __vite_injected_original_dirname = "C:\\Users\\Administrator.WIN-36O2UQRI3U1\\Desktop\\\u4E0A\u7EBF\u7F51\u7AD9\u5F00\u53D1\u5B8C\u6210\\\u4E0A\u7EBF\u7F51\u7AD9.worktrees\\agents-install-vscode-cline-deploy-strix\\frontend\\admin";
dns.setDefaultResultOrder("ipv4first");
var lanHost = (process.env.YOUDING_DEV_LAN_HOST || "").trim();
var vite_config_default = defineConfig(({ mode }) => ({
  base: "/",
  plugins: [
    vue(),
    vueJsx(),
    Components({
      dts: "src/components.d.ts",
      resolvers: [
        AntDesignVueResolver({
          importStyle: false
        })
      ]
    }),
    ...mode === "analyze" ? [
      visualizer({
        open: false,
        gzipSize: true,
        brotliSize: true
      })
    ] : []
  ],
  resolve: {
    alias: [
      // 注意:alias 数组,长前缀优先匹配(避免覆盖 @ 等)
      { find: /^~\//, replacement: resolve(__vite_injected_original_dirname, "..") + "/" },
      // ~/config/plan-catalog → frontend/config/plan-catalog
      { find: "@", replacement: resolve(__vite_injected_original_dirname, "src") + "/" },
      { find: "@marketing", replacement: resolve(__vite_injected_original_dirname, "../config/platform-marketing-content.ts") },
      { find: "@frontend-config", replacement: resolve(__vite_injected_original_dirname, "../config") + "/" }
    ]
  },
  server: {
    port: 5173,
    /** host:true + dns.setDefaultResultOrder('ipv4first') 确保同时监听 IPv4 */
    host: true,
    /** 允许手机通过局域网 IP 访问（Vite 5.4+ 默认会拦截非白名单 Host） */
    allowedHosts: true,
    /** 联机测试禁用 HMR：远端设备不需要热更新，且 HMR 重连易导致白屏/进程不稳定 */
    ...lanHost ? { hmr: false } : {},
    warmup: {
      clientFiles: [
        "./src/main.ts",
        "./src/App.vue",
        "./src/router/index.ts",
        "./src/layout/index.vue",
        "./src/stores/auth.ts",
        "./src/utils/api.ts",
        "./src/views/admin/system/overview.vue"
      ]
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        timeout: 6e5,
        proxyTimeout: 6e5,
        selfHandleResponse: true,
        configure: (proxy) => {
          proxy.on("proxyRes", (proxyRes, req, res) => {
            const rawSetCookies = [];
            const otherHeaders = {};
            for (let i = 0; i < proxyRes.rawHeaders.length; i += 2) {
              const name = proxyRes.rawHeaders[i].toLowerCase();
              const value = proxyRes.rawHeaders[i + 1];
              if (name === "set-cookie") {
                rawSetCookies.push(value);
              } else if (!otherHeaders[name]) {
                otherHeaders[name] = value;
              }
            }
            for (const [name, value] of Object.entries(otherHeaders)) {
              res.setHeader(name, value);
            }
            if (rawSetCookies.length > 0) {
              res.setHeader("set-cookie", rawSetCookies);
            }
            res.statusCode = proxyRes.statusCode ?? 502;
            proxyRes.pipe(res);
          });
        }
      },
      "/uploads": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      },
      "/socket.io": {
        target: "ws://127.0.0.1:8000",
        ws: true,
        changeOrigin: true
      },
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    target: "es2020",
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: false,
    minify: "esbuild",
    cssMinify: "esbuild",
    cssCodeSplit: true,
    modulePreload: { polyfill: false },
    reportCompressedSize: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/ant-design-vue")) return "antd";
          if (id.includes("node_modules/@ant-design")) return "antd-icons";
          if (id.includes("node_modules/vue") || id.includes("node_modules/vue-router") || id.includes("node_modules/pinia")) return "vue";
          if (id.includes("node_modules/echarts") || id.includes("node_modules/vue-echarts")) return "echarts";
          if (id.includes("/views/client/copilot.vue")) return "copilot";
          if (id.includes("/views/client/chuhaiji-app.vue")) return "chuhaiji-app";
          if (id.includes("/views/admin/") && !id.includes("/views/admin/system/")) return "admin";
          if (id.includes("/views/admin/system/")) return "admin-system";
          if (id.includes("/views/client/")) return "client";
          if (id.includes("/views/agent/")) return "agent";
          if (id.includes("/views/tenants/")) return "tenants";
          if (id.includes("node_modules/axios") || id.includes("node_modules/dayjs") || id.includes("node_modules/lodash")) return "utils";
          if (id.includes("node_modules")) return "vendor";
        },
        chunkFileNames: "js/[name]-[hash].js",
        entryFileNames: "js/[name]-[hash].js",
        assetFileNames: "[ext]/[name]-[hash].[ext]"
      }
    },
    chunkSizeWarningLimit: 500
  },
  optimizeDeps: {
    include: [
      "vue",
      "vue-router",
      "pinia",
      "axios",
      "ant-design-vue",
      "@ant-design/icons-vue",
      "dayjs",
      "dayjs/plugin/relativeTime"
    ]
  }
}));
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxBZG1pbmlzdHJhdG9yLldJTi0zNk8yVVFSSTNVMVxcXFxEZXNrdG9wXFxcXFx1NEUwQVx1N0VCRlx1N0Y1MVx1N0FEOVx1NUYwMFx1NTNEMVx1NUI4Q1x1NjIxMFxcXFxcdTRFMEFcdTdFQkZcdTdGNTFcdTdBRDkud29ya3RyZWVzXFxcXGFnZW50cy1pbnN0YWxsLXZzY29kZS1jbGluZS1kZXBsb3ktc3RyaXhcXFxcZnJvbnRlbmRcXFxcYWRtaW5cIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkM6XFxcXFVzZXJzXFxcXEFkbWluaXN0cmF0b3IuV0lOLTM2TzJVUVJJM1UxXFxcXERlc2t0b3BcXFxcXHU0RTBBXHU3RUJGXHU3RjUxXHU3QUQ5XHU1RjAwXHU1M0QxXHU1QjhDXHU2MjEwXFxcXFx1NEUwQVx1N0VCRlx1N0Y1MVx1N0FEOS53b3JrdHJlZXNcXFxcYWdlbnRzLWluc3RhbGwtdnNjb2RlLWNsaW5lLWRlcGxveS1zdHJpeFxcXFxmcm9udGVuZFxcXFxhZG1pblxcXFx2aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovVXNlcnMvQWRtaW5pc3RyYXRvci5XSU4tMzZPMlVRUkkzVTEvRGVza3RvcC8lRTQlQjglOEElRTclQkElQkYlRTclQkQlOTElRTclQUIlOTklRTUlQkMlODAlRTUlOEYlOTElRTUlQUUlOEMlRTYlODglOTAvJUU0JUI4JThBJUU3JUJBJUJGJUU3JUJEJTkxJUU3JUFCJTk5Lndvcmt0cmVlcy9hZ2VudHMtaW5zdGFsbC12c2NvZGUtY2xpbmUtZGVwbG95LXN0cml4L2Zyb250ZW5kL2FkbWluL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSc7XHJcbmltcG9ydCB2dWUgZnJvbSAnQHZpdGVqcy9wbHVnaW4tdnVlJztcclxuaW1wb3J0IHsgcmVzb2x2ZSB9IGZyb20gJ3BhdGgnO1xyXG5pbXBvcnQgdnVlSnN4IGZyb20gJ0B2aXRlanMvcGx1Z2luLXZ1ZS1qc3gnO1xyXG5pbXBvcnQgeyB2aXN1YWxpemVyIH0gZnJvbSAncm9sbHVwLXBsdWdpbi12aXN1YWxpemVyJztcclxuaW1wb3J0IGRucyBmcm9tICdub2RlOmRucyc7XHJcblxyXG4vLyBcdTVGM0FcdTUyMzYgTm9kZS5qcyBETlMgXHU4OUUzXHU2NzkwXHU0RjdGXHU3NTI4IElQdjRcdUZGMENcdTRGRUVcdTU5MEQgVFJBRSAvIE5vZGUgMjArIFx1NzNBRlx1NTg4M1x1NEUyRCBWaXRlIFx1NEVDNVx1NzZEMVx1NTQyQyBJUHY2IFx1NzY4NFx1OTVFRVx1OTg5OFxyXG5kbnMuc2V0RGVmYXVsdFJlc3VsdE9yZGVyKCdpcHY0Zmlyc3QnKTtcclxuXHJcbmltcG9ydCBDb21wb25lbnRzIGZyb20gJ3VucGx1Z2luLXZ1ZS1jb21wb25lbnRzL3ZpdGUnO1xyXG5pbXBvcnQgeyBBbnREZXNpZ25WdWVSZXNvbHZlciB9IGZyb20gJ3VucGx1Z2luLXZ1ZS1jb21wb25lbnRzL3Jlc29sdmVycyc7XHJcblxyXG5jb25zdCBsYW5Ib3N0ID0gKHByb2Nlc3MuZW52LllPVURJTkdfREVWX0xBTl9IT1NUIHx8ICcnKS50cmltKCk7XHJcblxyXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoKHsgbW9kZSB9KSA9PiAoe1xyXG4gIGJhc2U6ICcvJyxcclxuICBwbHVnaW5zOiBbXHJcbiAgICB2dWUoKSxcclxuICAgIHZ1ZUpzeCgpLFxyXG4gICAgQ29tcG9uZW50cyh7XHJcbiAgICAgIGR0czogJ3NyYy9jb21wb25lbnRzLmQudHMnLFxyXG4gICAgICByZXNvbHZlcnM6IFtcclxuICAgICAgICBBbnREZXNpZ25WdWVSZXNvbHZlcih7XHJcbiAgICAgICAgICBpbXBvcnRTdHlsZTogZmFsc2UsXHJcbiAgICAgICAgfSksXHJcbiAgICAgIF0sXHJcbiAgICB9KSxcclxuICAgIC4uLihtb2RlID09PSAnYW5hbHl6ZSdcclxuICAgICAgPyBbXHJcbiAgICAgICAgICB2aXN1YWxpemVyKHtcclxuICAgICAgICAgICAgb3BlbjogZmFsc2UsXHJcbiAgICAgICAgICAgIGd6aXBTaXplOiB0cnVlLFxyXG4gICAgICAgICAgICBicm90bGlTaXplOiB0cnVlLFxyXG4gICAgICAgICAgfSksXHJcbiAgICAgICAgXVxyXG4gICAgICA6IFtdKSxcclxuICBdLFxyXG4gIHJlc29sdmU6IHtcclxuICAgIGFsaWFzOiBbXHJcbiAgICAgIC8vIFx1NkNFOFx1NjEwRjphbGlhcyBcdTY1NzBcdTdFQzQsXHU5NTdGXHU1MjREXHU3RjAwXHU0RjE4XHU1MTQ4XHU1MzM5XHU5MTREKFx1OTA3Rlx1NTE0RFx1ODk4Nlx1NzZENiBAIFx1N0I0OSlcclxuICAgICAgeyBmaW5kOiAvXn5cXC8vLCByZXBsYWNlbWVudDogcmVzb2x2ZShfX2Rpcm5hbWUsICcuLicpICsgJy8nIH0sICAvLyB+L2NvbmZpZy9wbGFuLWNhdGFsb2cgXHUyMTkyIGZyb250ZW5kL2NvbmZpZy9wbGFuLWNhdGFsb2dcclxuICAgICAgeyBmaW5kOiAnQCcsIHJlcGxhY2VtZW50OiByZXNvbHZlKF9fZGlybmFtZSwgJ3NyYycpICsgJy8nIH0sXHJcbiAgICAgIHsgZmluZDogJ0BtYXJrZXRpbmcnLCByZXBsYWNlbWVudDogcmVzb2x2ZShfX2Rpcm5hbWUsICcuLi9jb25maWcvcGxhdGZvcm0tbWFya2V0aW5nLWNvbnRlbnQudHMnKSB9LFxyXG4gICAgICB7IGZpbmQ6ICdAZnJvbnRlbmQtY29uZmlnJywgcmVwbGFjZW1lbnQ6IHJlc29sdmUoX19kaXJuYW1lLCAnLi4vY29uZmlnJykgKyAnLycgfSxcclxuICAgIF0sXHJcbiAgfSxcclxuICBzZXJ2ZXI6IHtcclxuICAgIHBvcnQ6IDUxNzMsXHJcbiAgICAvKiogaG9zdDp0cnVlICsgZG5zLnNldERlZmF1bHRSZXN1bHRPcmRlcignaXB2NGZpcnN0JykgXHU3ODZFXHU0RkREXHU1NDBDXHU2NUY2XHU3NkQxXHU1NDJDIElQdjQgKi9cclxuICAgIGhvc3Q6IHRydWUsXHJcbiAgICAvKiogXHU1MTQxXHU4QkI4XHU2MjRCXHU2NzNBXHU5MDFBXHU4RkM3XHU1QzQwXHU1N0RGXHU3RjUxIElQIFx1OEJCRlx1OTVFRVx1RkYwOFZpdGUgNS40KyBcdTlFRDhcdThCQTRcdTRGMUFcdTYyRTZcdTYyMkFcdTk3NUVcdTc2N0RcdTU0MERcdTUzNTUgSG9zdFx1RkYwOSAqL1xyXG4gICAgYWxsb3dlZEhvc3RzOiB0cnVlLFxyXG4gICAgLyoqIFx1ODA1NFx1NjczQVx1NkQ0Qlx1OEJENVx1Nzk4MVx1NzUyOCBITVJcdUZGMUFcdThGRENcdTdBRUZcdThCQkVcdTU5MDdcdTRFMERcdTk3MDBcdTg5ODFcdTcwRURcdTY2RjRcdTY1QjBcdUZGMENcdTRFMTQgSE1SIFx1OTFDRFx1OEZERVx1NjYxM1x1NUJGQ1x1ODFGNFx1NzY3RFx1NUM0Ri9cdThGREJcdTdBMEJcdTRFMERcdTdBMzNcdTVCOUEgKi9cclxuICAgIC4uLihsYW5Ib3N0ID8geyBobXI6IGZhbHNlIH0gOiB7fSksXHJcbiAgICB3YXJtdXA6IHtcclxuICAgICAgY2xpZW50RmlsZXM6IFtcclxuICAgICAgICAnLi9zcmMvbWFpbi50cycsXHJcbiAgICAgICAgJy4vc3JjL0FwcC52dWUnLFxyXG4gICAgICAgICcuL3NyYy9yb3V0ZXIvaW5kZXgudHMnLFxyXG4gICAgICAgICcuL3NyYy9sYXlvdXQvaW5kZXgudnVlJyxcclxuICAgICAgICAnLi9zcmMvc3RvcmVzL2F1dGgudHMnLFxyXG4gICAgICAgICcuL3NyYy91dGlscy9hcGkudHMnLFxyXG4gICAgICAgICcuL3NyYy92aWV3cy9hZG1pbi9zeXN0ZW0vb3ZlcnZpZXcudnVlJyxcclxuICAgICAgXSxcclxuICAgIH0sXHJcbiAgICBwcm94eToge1xyXG4gICAgICAnL2FwaSc6IHtcclxuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vMTI3LjAuMC4xOjgwMDAnLFxyXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZSxcclxuICAgICAgICB0aW1lb3V0OiA2MDBfMDAwLFxyXG4gICAgICAgIHByb3h5VGltZW91dDogNjAwXzAwMCxcclxuICAgICAgICBzZWxmSGFuZGxlUmVzcG9uc2U6IHRydWUsXHJcbiAgICAgICAgY29uZmlndXJlOiAocHJveHkpID0+IHtcclxuICAgICAgICAgIC8vIFx1NUI4Q1x1NTE2OFx1NjI0Qlx1NTJBOFx1NTkwNFx1NzQwNlx1NEVFM1x1NzQwNlx1NTRDRFx1NUU5NFx1RkYwQ1x1NEZFRVx1NTkwRFx1NTkxQVx1NEUyQSBTZXQtQ29va2llIFx1NTkzNFx1ODhBQlx1NTQwOFx1NUU3Nlx1NzY4NFx1OTVFRVx1OTg5OFxyXG4gICAgICAgICAgcHJveHkub24oJ3Byb3h5UmVzJywgKHByb3h5UmVzLCByZXEsIHJlcykgPT4ge1xyXG4gICAgICAgICAgICAvLyBcdTRFQ0UgcmF3SGVhZGVycyBcdTYzRDBcdTUzRDZcdTYyNDBcdTY3MDkgU2V0LUNvb2tpZVx1RkYwOE5vZGUuanMgaGVhZGVycyBcdTVCRjlcdThDNjFcdTRGMUFcdTU0MDhcdTVFNzZcdTU0MENcdTU0MERcdTU5MzRcdUZGMDlcclxuICAgICAgICAgICAgY29uc3QgcmF3U2V0Q29va2llczogc3RyaW5nW10gPSBbXTtcclxuICAgICAgICAgICAgY29uc3Qgb3RoZXJIZWFkZXJzOiBSZWNvcmQ8c3RyaW5nLCBzdHJpbmc+ID0ge307XHJcbiAgICAgICAgICAgIGZvciAobGV0IGkgPSAwOyBpIDwgcHJveHlSZXMucmF3SGVhZGVycy5sZW5ndGg7IGkgKz0gMikge1xyXG4gICAgICAgICAgICAgIGNvbnN0IG5hbWUgPSBwcm94eVJlcy5yYXdIZWFkZXJzW2ldLnRvTG93ZXJDYXNlKCk7XHJcbiAgICAgICAgICAgICAgY29uc3QgdmFsdWUgPSBwcm94eVJlcy5yYXdIZWFkZXJzW2kgKyAxXTtcclxuICAgICAgICAgICAgICBpZiAobmFtZSA9PT0gJ3NldC1jb29raWUnKSB7XHJcbiAgICAgICAgICAgICAgICByYXdTZXRDb29raWVzLnB1c2godmFsdWUpO1xyXG4gICAgICAgICAgICAgIH0gZWxzZSBpZiAoIW90aGVySGVhZGVyc1tuYW1lXSkge1xyXG4gICAgICAgICAgICAgICAgb3RoZXJIZWFkZXJzW25hbWVdID0gdmFsdWU7XHJcbiAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIC8vIFx1OEJCRVx1N0Y2RVx1NjY2RVx1OTAxQVx1NTkzNFxyXG4gICAgICAgICAgICBmb3IgKGNvbnN0IFtuYW1lLCB2YWx1ZV0gb2YgT2JqZWN0LmVudHJpZXMob3RoZXJIZWFkZXJzKSkge1xyXG4gICAgICAgICAgICAgIHJlcy5zZXRIZWFkZXIobmFtZSwgdmFsdWUpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIC8vIFx1OEJCRVx1N0Y2RVx1NjI0MFx1NjcwOSBTZXQtQ29va2llIFx1NEUzQVx1NjU3MFx1N0VDNFxyXG4gICAgICAgICAgICBpZiAocmF3U2V0Q29va2llcy5sZW5ndGggPiAwKSB7XHJcbiAgICAgICAgICAgICAgcmVzLnNldEhlYWRlcignc2V0LWNvb2tpZScsIHJhd1NldENvb2tpZXMpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIHJlcy5zdGF0dXNDb2RlID0gcHJveHlSZXMuc3RhdHVzQ29kZSA/PyA1MDI7XHJcbiAgICAgICAgICAgIHByb3h5UmVzLnBpcGUocmVzKTtcclxuICAgICAgICAgIH0pO1xyXG4gICAgICAgIH0sXHJcbiAgICAgIH0sXHJcbiAgICAgICcvdXBsb2Fkcyc6IHtcclxuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vMTI3LjAuMC4xOjgwMDAnLFxyXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZSxcclxuICAgICAgfSxcclxuICAgICAgJy9zb2NrZXQuaW8nOiB7XHJcbiAgICAgICAgdGFyZ2V0OiAnd3M6Ly8xMjcuMC4wLjE6ODAwMCcsXHJcbiAgICAgICAgd3M6IHRydWUsXHJcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxyXG4gICAgICB9LFxyXG4gICAgICAnL3dzJzoge1xyXG4gICAgICAgIHRhcmdldDogJ3dzOi8vMTI3LjAuMC4xOjgwMDAnLFxyXG4gICAgICAgIHdzOiB0cnVlLFxyXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZSxcclxuICAgICAgfSxcclxuICAgIH0sXHJcbiAgfSxcclxuICBidWlsZDoge1xyXG4gICAgdGFyZ2V0OiAnZXMyMDIwJyxcclxuICAgIG91dERpcjogJ2Rpc3QnLFxyXG4gICAgYXNzZXRzRGlyOiAnYXNzZXRzJyxcclxuICAgIHNvdXJjZW1hcDogZmFsc2UsXHJcbiAgICBtaW5pZnk6ICdlc2J1aWxkJyxcclxuICAgIGNzc01pbmlmeTogJ2VzYnVpbGQnLFxyXG4gICAgY3NzQ29kZVNwbGl0OiB0cnVlLFxyXG4gICAgbW9kdWxlUHJlbG9hZDogeyBwb2x5ZmlsbDogZmFsc2UgfSxcclxuICAgIHJlcG9ydENvbXByZXNzZWRTaXplOiBmYWxzZSxcclxuICAgIHJvbGx1cE9wdGlvbnM6IHtcclxuICAgICAgb3V0cHV0OiB7XHJcbiAgICAgICAgbWFudWFsQ2h1bmtzKGlkKSB7XHJcbiAgICAgICAgICBpZiAoaWQuaW5jbHVkZXMoJ25vZGVfbW9kdWxlcy9hbnQtZGVzaWduLXZ1ZScpKSByZXR1cm4gJ2FudGQnO1xyXG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvQGFudC1kZXNpZ24nKSkgcmV0dXJuICdhbnRkLWljb25zJztcclxuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzL3Z1ZScpIHx8IGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvdnVlLXJvdXRlcicpIHx8IGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvcGluaWEnKSkgcmV0dXJuICd2dWUnO1xyXG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvZWNoYXJ0cycpIHx8IGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvdnVlLWVjaGFydHMnKSkgcmV0dXJuICdlY2hhcnRzJztcclxuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnL3ZpZXdzL2NsaWVudC9jb3BpbG90LnZ1ZScpKSByZXR1cm4gJ2NvcGlsb3QnO1xyXG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCcvdmlld3MvY2xpZW50L2NodWhhaWppLWFwcC52dWUnKSkgcmV0dXJuICdjaHVoYWlqaS1hcHAnO1xyXG4gICAgICAgICAgLy8gRklYLTI3OiBcdTYzMDlcdTg5RDJcdTgyNzJcdTU4RjNcdTYyQzZcdTUyMDZcdThERUZcdTc1MzEgY2h1bmtcdUZGMENcdTUxQ0ZcdTVDMTFcdTk5OTZcdTZCMjFcdTUyQTBcdThGN0RcdTRGNTNcdTc5RUZcclxuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnL3ZpZXdzL2FkbWluLycpICYmICFpZC5pbmNsdWRlcygnL3ZpZXdzL2FkbWluL3N5c3RlbS8nKSkgcmV0dXJuICdhZG1pbic7XHJcbiAgICAgICAgICBpZiAoaWQuaW5jbHVkZXMoJy92aWV3cy9hZG1pbi9zeXN0ZW0vJykpIHJldHVybiAnYWRtaW4tc3lzdGVtJztcclxuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnL3ZpZXdzL2NsaWVudC8nKSkgcmV0dXJuICdjbGllbnQnO1xyXG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCcvdmlld3MvYWdlbnQvJykpIHJldHVybiAnYWdlbnQnO1xyXG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCcvdmlld3MvdGVuYW50cy8nKSkgcmV0dXJuICd0ZW5hbnRzJztcclxuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzL2F4aW9zJykgfHwgaWQuaW5jbHVkZXMoJ25vZGVfbW9kdWxlcy9kYXlqcycpIHx8IGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvbG9kYXNoJykpIHJldHVybiAndXRpbHMnO1xyXG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMnKSkgcmV0dXJuICd2ZW5kb3InO1xyXG4gICAgICAgIH0sXHJcbiAgICAgICAgY2h1bmtGaWxlTmFtZXM6ICdqcy9bbmFtZV0tW2hhc2hdLmpzJyxcclxuICAgICAgICBlbnRyeUZpbGVOYW1lczogJ2pzL1tuYW1lXS1baGFzaF0uanMnLFxyXG4gICAgICAgIGFzc2V0RmlsZU5hbWVzOiAnW2V4dF0vW25hbWVdLVtoYXNoXS5bZXh0XScsXHJcbiAgICAgIH0sXHJcbiAgICB9LFxyXG4gICAgY2h1bmtTaXplV2FybmluZ0xpbWl0OiA1MDAsXHJcbiAgfSxcclxuICBvcHRpbWl6ZURlcHM6IHtcclxuICAgIGluY2x1ZGU6IFtcclxuICAgICAgJ3Z1ZScsXHJcbiAgICAgICd2dWUtcm91dGVyJyxcclxuICAgICAgJ3BpbmlhJyxcclxuICAgICAgJ2F4aW9zJyxcclxuICAgICAgJ2FudC1kZXNpZ24tdnVlJyxcclxuICAgICAgJ0BhbnQtZGVzaWduL2ljb25zLXZ1ZScsXHJcbiAgICAgICdkYXlqcycsXHJcbiAgICAgICdkYXlqcy9wbHVnaW4vcmVsYXRpdmVUaW1lJyxcclxuICAgIF0sXHJcbiAgfSxcclxufSkpO1xyXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQThwQixTQUFTLG9CQUFvQjtBQUMzckIsT0FBTyxTQUFTO0FBQ2hCLFNBQVMsZUFBZTtBQUN4QixPQUFPLFlBQVk7QUFDbkIsU0FBUyxrQkFBa0I7QUFDM0IsT0FBTyxTQUFTO0FBS2hCLE9BQU8sZ0JBQWdCO0FBQ3ZCLFNBQVMsNEJBQTRCO0FBWHJDLElBQU0sbUNBQW1DO0FBUXpDLElBQUksc0JBQXNCLFdBQVc7QUFLckMsSUFBTSxXQUFXLFFBQVEsSUFBSSx3QkFBd0IsSUFBSSxLQUFLO0FBRTlELElBQU8sc0JBQVEsYUFBYSxDQUFDLEVBQUUsS0FBSyxPQUFPO0FBQUEsRUFDekMsTUFBTTtBQUFBLEVBQ04sU0FBUztBQUFBLElB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
