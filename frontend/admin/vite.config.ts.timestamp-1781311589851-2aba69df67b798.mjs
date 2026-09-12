// vite.config.ts
import { defineConfig } from "file:///C:/Users/97907/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99/frontend/admin/node_modules/vite/dist/node/index.js";
import vue from "file:///C:/Users/97907/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99/frontend/admin/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { resolve } from "path";
import vueJsx from "file:///C:/Users/97907/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99/frontend/admin/node_modules/@vitejs/plugin-vue-jsx/dist/index.mjs";
import { visualizer } from "file:///C:/Users/97907/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99/frontend/admin/node_modules/rollup-plugin-visualizer/dist/plugin/index.js";
import Components from "file:///C:/Users/97907/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99/frontend/admin/node_modules/unplugin-vue-components/dist/vite.js";
import { AntDesignVueResolver } from "file:///C:/Users/97907/Desktop/%E4%B8%8A%E7%BA%BF%E7%BD%91%E7%AB%99/frontend/admin/node_modules/unplugin-vue-components/dist/resolvers.js";
var __vite_injected_original_dirname = "C:\\Users\\97907\\Desktop\\\u4E0A\u7EBF\u7F51\u7AD9\\frontend\\admin";
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
    /** 同时监听 IPv4/局域网，避免仅用 localhost 时部分环境「打不开」 */
    host: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true
      },
      "/uploads": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true
      },
      "/socket.io": {
        target: "ws://127.0.0.1:8001",
        ws: true,
        changeOrigin: true
      },
      "/ws": {
        target: "ws://127.0.0.1:8001",
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
    include: ["vue", "vue-router", "pinia", "axios", "ant-design-vue", "@ant-design/icons-vue"]
  }
}));
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFw5NzkwN1xcXFxEZXNrdG9wXFxcXFx1NEUwQVx1N0VCRlx1N0Y1MVx1N0FEOVxcXFxmcm9udGVuZFxcXFxhZG1pblwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcVXNlcnNcXFxcOTc5MDdcXFxcRGVza3RvcFxcXFxcdTRFMEFcdTdFQkZcdTdGNTFcdTdBRDlcXFxcZnJvbnRlbmRcXFxcYWRtaW5cXFxcdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L1VzZXJzLzk3OTA3L0Rlc2t0b3AvJUU0JUI4JThBJUU3JUJBJUJGJUU3JUJEJTkxJUU3JUFCJTk5L2Zyb250ZW5kL2FkbWluL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSc7XG5pbXBvcnQgdnVlIGZyb20gJ0B2aXRlanMvcGx1Z2luLXZ1ZSc7XG5pbXBvcnQgeyByZXNvbHZlIH0gZnJvbSAncGF0aCc7XG5pbXBvcnQgdnVlSnN4IGZyb20gJ0B2aXRlanMvcGx1Z2luLXZ1ZS1qc3gnO1xuaW1wb3J0IHsgdmlzdWFsaXplciB9IGZyb20gJ3JvbGx1cC1wbHVnaW4tdmlzdWFsaXplcic7XG5pbXBvcnQgQ29tcG9uZW50cyBmcm9tICd1bnBsdWdpbi12dWUtY29tcG9uZW50cy92aXRlJztcbmltcG9ydCB7IEFudERlc2lnblZ1ZVJlc29sdmVyIH0gZnJvbSAndW5wbHVnaW4tdnVlLWNvbXBvbmVudHMvcmVzb2x2ZXJzJztcblxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKCh7IG1vZGUgfSkgPT4gKHtcbiAgYmFzZTogJy8nLFxuICBwbHVnaW5zOiBbXG4gICAgdnVlKCksXG4gICAgdnVlSnN4KCksXG4gICAgQ29tcG9uZW50cyh7XG4gICAgICBkdHM6ICdzcmMvY29tcG9uZW50cy5kLnRzJyxcbiAgICAgIHJlc29sdmVyczogW1xuICAgICAgICBBbnREZXNpZ25WdWVSZXNvbHZlcih7XG4gICAgICAgICAgaW1wb3J0U3R5bGU6IGZhbHNlLFxuICAgICAgICB9KSxcbiAgICAgIF0sXG4gICAgfSksXG4gICAgLi4uKG1vZGUgPT09ICdhbmFseXplJ1xuICAgICAgPyBbXG4gICAgICAgICAgdmlzdWFsaXplcih7XG4gICAgICAgICAgICBvcGVuOiBmYWxzZSxcbiAgICAgICAgICAgIGd6aXBTaXplOiB0cnVlLFxuICAgICAgICAgICAgYnJvdGxpU2l6ZTogdHJ1ZSxcbiAgICAgICAgICB9KSxcbiAgICAgICAgXVxuICAgICAgOiBbXSksXG4gIF0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczogW1xuICAgICAgLy8gXHU2Q0U4XHU2MTBGOmFsaWFzIFx1NjU3MFx1N0VDNCxcdTk1N0ZcdTUyNERcdTdGMDBcdTRGMThcdTUxNDhcdTUzMzlcdTkxNEQoXHU5MDdGXHU1MTREXHU4OTg2XHU3NkQ2IEAgXHU3QjQ5KVxuICAgICAgeyBmaW5kOiAvXn5cXC8vLCByZXBsYWNlbWVudDogcmVzb2x2ZShfX2Rpcm5hbWUsICcuLicpICsgJy8nIH0sICAvLyB+L2NvbmZpZy9wbGFuLWNhdGFsb2cgXHUyMTkyIGZyb250ZW5kL2NvbmZpZy9wbGFuLWNhdGFsb2dcbiAgICAgIHsgZmluZDogJ0AnLCByZXBsYWNlbWVudDogcmVzb2x2ZShfX2Rpcm5hbWUsICdzcmMnKSArICcvJyB9LFxuICAgICAgeyBmaW5kOiAnQG1hcmtldGluZycsIHJlcGxhY2VtZW50OiByZXNvbHZlKF9fZGlybmFtZSwgJy4uL2NvbmZpZy9wbGF0Zm9ybS1tYXJrZXRpbmctY29udGVudC50cycpIH0sXG4gICAgICB7IGZpbmQ6ICdAZnJvbnRlbmQtY29uZmlnJywgcmVwbGFjZW1lbnQ6IHJlc29sdmUoX19kaXJuYW1lLCAnLi4vY29uZmlnJykgKyAnLycgfSxcbiAgICBdLFxuICB9LFxuICBzZXJ2ZXI6IHtcbiAgICBwb3J0OiA1MTczLFxuICAgIC8qKiBcdTU0MENcdTY1RjZcdTc2RDFcdTU0MkMgSVB2NC9cdTVDNDBcdTU3REZcdTdGNTFcdUZGMENcdTkwN0ZcdTUxNERcdTRFQzVcdTc1MjggbG9jYWxob3N0IFx1NjVGNlx1OTBFOFx1NTIwNlx1NzNBRlx1NTg4M1x1MzAwQ1x1NjI1M1x1NEUwRFx1NUYwMFx1MzAwRCAqL1xuICAgIGhvc3Q6IHRydWUsXG4gICAgcHJveHk6IHtcbiAgICAgICcvYXBpJzoge1xuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vMTI3LjAuMC4xOjgwMDEnLFxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXG4gICAgICB9LFxuICAgICAgJy91cGxvYWRzJzoge1xuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vMTI3LjAuMC4xOjgwMDEnLFxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXG4gICAgICB9LFxuICAgICAgJy9zb2NrZXQuaW8nOiB7XG4gICAgICAgIHRhcmdldDogJ3dzOi8vMTI3LjAuMC4xOjgwMDEnLFxuICAgICAgICB3czogdHJ1ZSxcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgfSxcbiAgICAgICcvd3MnOiB7XG4gICAgICAgIHRhcmdldDogJ3dzOi8vMTI3LjAuMC4xOjgwMDEnLFxuICAgICAgICB3czogdHJ1ZSxcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgfSxcbiAgICB9LFxuICB9LFxuICBidWlsZDoge1xuICAgIHRhcmdldDogJ2VzMjAyMCcsXG4gICAgb3V0RGlyOiAnZGlzdCcsXG4gICAgYXNzZXRzRGlyOiAnYXNzZXRzJyxcbiAgICBzb3VyY2VtYXA6IGZhbHNlLFxuICAgIG1pbmlmeTogJ2VzYnVpbGQnLFxuICAgIGNzc01pbmlmeTogJ2VzYnVpbGQnLFxuICAgIGNzc0NvZGVTcGxpdDogdHJ1ZSxcbiAgICBtb2R1bGVQcmVsb2FkOiB7IHBvbHlmaWxsOiBmYWxzZSB9LFxuICAgIHJlcG9ydENvbXByZXNzZWRTaXplOiBmYWxzZSxcbiAgICByb2xsdXBPcHRpb25zOiB7XG4gICAgICBvdXRwdXQ6IHtcbiAgICAgICAgbWFudWFsQ2h1bmtzKGlkKSB7XG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvYW50LWRlc2lnbi12dWUnKSkgcmV0dXJuICdhbnRkJztcbiAgICAgICAgICBpZiAoaWQuaW5jbHVkZXMoJ25vZGVfbW9kdWxlcy9AYW50LWRlc2lnbicpKSByZXR1cm4gJ2FudGQtaWNvbnMnO1xuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzL3Z1ZScpIHx8IGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvdnVlLXJvdXRlcicpIHx8IGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvcGluaWEnKSkgcmV0dXJuICd2dWUnO1xuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzL2VjaGFydHMnKSB8fCBpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzL3Z1ZS1lY2hhcnRzJykpIHJldHVybiAnZWNoYXJ0cyc7XG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCcvdmlld3MvY2xpZW50L2NvcGlsb3QudnVlJykpIHJldHVybiAnY29waWxvdCc7XG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCcvdmlld3MvY2xpZW50L2NodWhhaWppLWFwcC52dWUnKSkgcmV0dXJuICdjaHVoYWlqaS1hcHAnO1xuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzL2F4aW9zJykgfHwgaWQuaW5jbHVkZXMoJ25vZGVfbW9kdWxlcy9kYXlqcycpIHx8IGlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMvbG9kYXNoJykpIHJldHVybiAndXRpbHMnO1xuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzJykpIHJldHVybiAndmVuZG9yJztcbiAgICAgICAgfSxcbiAgICAgICAgY2h1bmtGaWxlTmFtZXM6ICdqcy9bbmFtZV0tW2hhc2hdLmpzJyxcbiAgICAgICAgZW50cnlGaWxlTmFtZXM6ICdqcy9bbmFtZV0tW2hhc2hdLmpzJyxcbiAgICAgICAgYXNzZXRGaWxlTmFtZXM6ICdbZXh0XS9bbmFtZV0tW2hhc2hdLltleHRdJyxcbiAgICAgIH0sXG4gICAgfSxcbiAgICBjaHVua1NpemVXYXJuaW5nTGltaXQ6IDUwMCxcbiAgfSxcbiAgb3B0aW1pemVEZXBzOiB7XG4gICAgaW5jbHVkZTogWyd2dWUnLCAndnVlLXJvdXRlcicsICdwaW5pYScsICdheGlvcycsICdhbnQtZGVzaWduLXZ1ZScsICdAYW50LWRlc2lnbi9pY29ucy12dWUnXSxcbiAgfSxcbn0pKTtcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBOFYsU0FBUyxvQkFBb0I7QUFDM1gsT0FBTyxTQUFTO0FBQ2hCLFNBQVMsZUFBZTtBQUN4QixPQUFPLFlBQVk7QUFDbkIsU0FBUyxrQkFBa0I7QUFDM0IsT0FBTyxnQkFBZ0I7QUFDdkIsU0FBUyw0QkFBNEI7QUFOckMsSUFBTSxtQ0FBbUM7QUFRekMsSUFBTyxzQkFBUSxhQUFhLENBQUMsRUFBRSxLQUFLLE9BQU87QUFBQSxFQUN6QyxNQUFNO0FBQUEsRUFDTixTQUFTO0FBQUEsSUFDUCxJQUFJO0FBQUEsSUFDSixPQUFPO0FBQUEsSUFDUCxXQUFXO0FBQUEsTUFDVCxLQUFLO0FBQUEsTUFDTCxXQUFXO0FBQUEsUUFDVCxxQkFBcUI7QUFBQSxVQUNuQixhQUFhO0FBQUEsUUFDZixDQUFDO0FBQUEsTUFDSDtBQUFBLElBQ0YsQ0FBQztBQUFBLElBQ0QsR0FBSSxTQUFTLFlBQ1Q7QUFBQSxNQUNFLFdBQVc7QUFBQSxRQUNULE1BQU07QUFBQSxRQUNOLFVBQVU7QUFBQSxRQUNWLFlBQVk7QUFBQSxNQUNkLENBQUM7QUFBQSxJQUNILElBQ0EsQ0FBQztBQUFBLEVBQ1A7QUFBQSxFQUNBLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQTtBQUFBLE1BRUwsRUFBRSxNQUFNLFFBQVEsYUFBYSxRQUFRLGtDQUFXLElBQUksSUFBSSxJQUFJO0FBQUE7QUFBQSxNQUM1RCxFQUFFLE1BQU0sS0FBSyxhQUFhLFFBQVEsa0NBQVcsS0FBSyxJQUFJLElBQUk7QUFBQSxNQUMxRCxFQUFFLE1BQU0sY0FBYyxhQUFhLFFBQVEsa0NBQVcseUNBQXlDLEVBQUU7QUFBQSxNQUNqRyxFQUFFLE1BQU0sb0JBQW9CLGFBQWEsUUFBUSxrQ0FBVyxXQUFXLElBQUksSUFBSTtBQUFBLElBQ2pGO0FBQUEsRUFDRjtBQUFBLEVBQ0EsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBO0FBQUEsSUFFTixNQUFNO0FBQUEsSUFDTixPQUFPO0FBQUEsTUFDTCxRQUFRO0FBQUEsUUFDTixRQUFRO0FBQUEsUUFDUixjQUFjO0FBQUEsTUFDaEI7QUFBQSxNQUNBLFlBQVk7QUFBQSxRQUNWLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBLE1BQ0EsY0FBYztBQUFBLFFBQ1osUUFBUTtBQUFBLFFBQ1IsSUFBSTtBQUFBLFFBQ0osY0FBYztBQUFBLE1BQ2hCO0FBQUEsTUFDQSxPQUFPO0FBQUEsUUFDTCxRQUFRO0FBQUEsUUFDUixJQUFJO0FBQUEsUUFDSixjQUFjO0FBQUEsTUFDaEI7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBLEVBQ0EsT0FBTztBQUFBLElBQ0wsUUFBUTtBQUFBLElBQ1IsUUFBUTtBQUFBLElBQ1IsV0FBVztBQUFBLElBQ1gsV0FBVztBQUFBLElBQ1gsUUFBUTtBQUFBLElBQ1IsV0FBVztBQUFBLElBQ1gsY0FBYztBQUFBLElBQ2QsZUFBZSxFQUFFLFVBQVUsTUFBTTtBQUFBLElBQ2pDLHNCQUFzQjtBQUFBLElBQ3RCLGVBQWU7QUFBQSxNQUNiLFFBQVE7QUFBQSxRQUNOLGFBQWEsSUFBSTtBQUNmLGNBQUksR0FBRyxTQUFTLDZCQUE2QixFQUFHLFFBQU87QUFDdkQsY0FBSSxHQUFHLFNBQVMsMEJBQTBCLEVBQUcsUUFBTztBQUNwRCxjQUFJLEdBQUcsU0FBUyxrQkFBa0IsS0FBSyxHQUFHLFNBQVMseUJBQXlCLEtBQUssR0FBRyxTQUFTLG9CQUFvQixFQUFHLFFBQU87QUFDM0gsY0FBSSxHQUFHLFNBQVMsc0JBQXNCLEtBQUssR0FBRyxTQUFTLDBCQUEwQixFQUFHLFFBQU87QUFDM0YsY0FBSSxHQUFHLFNBQVMsMkJBQTJCLEVBQUcsUUFBTztBQUNyRCxjQUFJLEdBQUcsU0FBUyxnQ0FBZ0MsRUFBRyxRQUFPO0FBQzFELGNBQUksR0FBRyxTQUFTLG9CQUFvQixLQUFLLEdBQUcsU0FBUyxvQkFBb0IsS0FBSyxHQUFHLFNBQVMscUJBQXFCLEVBQUcsUUFBTztBQUN6SCxjQUFJLEdBQUcsU0FBUyxjQUFjLEVBQUcsUUFBTztBQUFBLFFBQzFDO0FBQUEsUUFDQSxnQkFBZ0I7QUFBQSxRQUNoQixnQkFBZ0I7QUFBQSxRQUNoQixnQkFBZ0I7QUFBQSxNQUNsQjtBQUFBLElBQ0Y7QUFBQSxJQUNBLHVCQUF1QjtBQUFBLEVBQ3pCO0FBQUEsRUFDQSxjQUFjO0FBQUEsSUFDWixTQUFTLENBQUMsT0FBTyxjQUFjLFNBQVMsU0FBUyxrQkFBa0IsdUJBQXVCO0FBQUEsRUFDNUY7QUFDRixFQUFFOyIsCiAgIm5hbWVzIjogW10KfQo=
