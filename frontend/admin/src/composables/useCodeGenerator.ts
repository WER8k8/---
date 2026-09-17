/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, computed } from 'vue';

export type CodeLanguage = 'vue' | 'typescript' | 'python' | 'html';

const LANGUAGE_LABEL: Record<CodeLanguage, string> = {
  vue: 'Vue 3',
  typescript: 'TypeScript',
  python: 'Python',
  html: 'HTML',
};

export interface CodeSnippetTemplate {
  id: string;
  title: string;
  language: CodeLanguage;
  body: string;
}

const SNIPPETS: CodeSnippetTemplate[] = [
  {
    id: 'vue-sfc',
    title: 'Vue SFC 骨架',
    language: 'vue',
    body: `<script setup lang="ts">
defineProps<{ title: string }>()
</script>

<template>
  <section class="p-4">
    <h1>{{ title }}</h1>
  </section>
</template>
`,
  },
  {
    id: 'ts-fetch',
    title: 'fetch 封装',
    language: 'typescript',
    body: `export async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(\`HTTP \${res.status}\`)
  return (await res.json()) as T
}
`,
  },
  {
    id: 'py-fastapi',
    title: 'FastAPI 路由',
    language: 'python',
    body: `from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
`,
  },
];

function buildStub(language: CodeLanguage, userPrompt: string): string {
  const hint = userPrompt.trim() || '（未填写需求，以下为占位示例）';
  const blocks: Record<CodeLanguage, string> = {
    vue: `<!-- 占位输出：接入后端模型后可替换 -->
<script setup lang="ts">
// ${hint}
const message = 'Hello from generator'
</script>

<template>
  <p>{{ message }}</p>
</template>
`,
    typescript: `// 占位输出 · 需求摘要: ${hint.replace(/\n/g, ' ')}\n\nexport function generated(): string {\n  return 'ok'\n}\n`,
    python: `# 占位输出 · 需求摘要: ${hint.replace(/\n/g, ' ')}\n\ndef generated():\n    return "ok"\n`,
    html: `<!-- 占位输出 · 需求: ${hint.replace(/</g, '')} -->\n<section class="stack">\n  <h2>生成区块</h2>\n  <p>在此处渲染模型输出。</p>\n</section>\n`,
  };
  return blocks[language];
}

export function useCodeGenerator() {
  const language = ref<CodeLanguage>('vue');
  const prompt = ref('');
  const output = ref('');
  const busy = ref(false);

  const languageLabel = computed(() => LANGUAGE_LABEL[language.value]);

  async function generate() {
    busy.value = true;
    output.value = '';
    try {
      await new Promise((r) => setTimeout(r, 280));
      output.value = buildStub(language.value, prompt.value);
    } finally {
      busy.value = false;
    }
  }

  function applyTemplate(t: CodeSnippetTemplate) {
    language.value = t.language;
    output.value = t.body;
  }

  function clearOutput() {
    output.value = '';
  }

  return {
    language,
    prompt,
    output,
    busy,
    languageLabel,
    snippets: SNIPPETS,
    generate,
    applyTemplate,
    clearOutput,
  };
}
