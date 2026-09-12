import type { Editor } from 'grapesjs';

import { grapesjsLocaleZh } from './grapesjsLocaleZh';

/** 初始化后：强制中文标签 + 替换 preset 区块默认英文占位 */
export function localizeGrapesEditor(editor: Editor): void {
  editor.I18n.addMessages({ zh: grapesjsLocaleZh });
  editor.I18n.setLocale('zh');

  const bm = editor.BlockManager;

  const blockLabels: Record<string, string> = {
    'link-block': '链接容器',
    quote: '引用段落',
    'text-basic': '标题+正文',
  };

  for (const [id, label] of Object.entries(blockLabels)) {
    const block = bm.get(id);
    if (block) block.set('label', label);
  }

  const categoryLabels: Record<string, string> = {
    Basic: '基础组件',
  };
  bm.getCategories().forEach((cat: any) => {
    const id = String(cat.get('id') ?? '');
    const label = String(cat.get('label') ?? '');
    const zh = categoryLabels[id] || categoryLabels[label];
    if (zh) cat.set('label', zh);
  });

  const quote = bm.get('quote');
  if (quote) {
    quote.set(
      'content',
      `<blockquote class="quote">
        在此填写客户评价或企业理念引用文字。
      </blockquote>`,
    );
  }

  const textBasic = bm.get('text-basic');
  if (textBasic) {
    textBasic.set(
      'content',
      `<section class="bdg-sect">
        <h1 class="heading">在此填写主标题</h1>
        <p class="paragraph">在此填写段落说明，介绍产品优势、工厂实力或服务能力。</p>
      </section>`,
    );
  }
}
