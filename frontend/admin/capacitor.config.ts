import type { CapacitorConfig } from '@capacitor/cli'

/** 出海计 App 壳 — 执行 npm i @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios 后 npx cap sync */
const config: CapacitorConfig = {
  appId: 'com.youding.chuhaiji',
  appName: '出海计',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
}

export default config
