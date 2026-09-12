import type { ISchema } from '@formily/json-schema';

/** 建站工作台 · SEO 三轨：Google 英文 / 百度中文 / Yandex 俄语 */
export const siteEditorSeoSchema: ISchema = {
  type: 'object',
  properties: {
    seoPrimaryMarket: {
      type: 'string',
      title: '默认收录市场',
      description: '决定 hreflang x-default 与首选站长平台',
      enum: ['export', 'domestic', 'russia'],
      default: 'export',
      'x-decorator': 'FormItem',
      'x-component': 'Select',
      'x-component-props': {
        options: [
          { label: 'Google / 全球出口（x-default → 英文）', value: 'export' },
          { label: '百度 / 中国国内（x-default → 中文）', value: 'domestic' },
          { label: 'Yandex / 俄罗斯（x-default → 俄语）', value: 'russia' },
        ],
      },
    },
    pageTitle: {
      type: 'string',
      title: 'Google 搜索标题（英文）',
      description: 'Google、Bing 等国际搜索；建议 Manufacturer / Supplier',
      'x-decorator': 'FormItem',
      'x-component': 'Input',
      'x-component-props': { placeholder: 'e.g. Rock Wool Manufacturer · Supplier' },
    },
    seoDescription: {
      type: 'string',
      title: 'Google 搜索简介（英文）',
      'x-decorator': 'FormItem',
      'x-component': 'TextArea',
      'x-component-props': { rows: 2, maxlength: 160 },
    },
    seoKeywords: {
      type: 'string',
      title: 'Google 关键词（英文）',
      'x-decorator': 'FormItem',
      'x-component': 'Input',
      'x-component-props': { placeholder: 'rock wool, insulation, OEM' },
    },
    domesticPageTitle: {
      type: 'string',
      title: '百度搜索标题（中文）',
      'x-decorator': 'FormItem',
      'x-component': 'Input',
      'x-component-props': { placeholder: '岩棉板生产厂家 · 供应商' },
    },
    domesticSeoDescription: {
      type: 'string',
      title: '百度搜索简介（中文）',
      'x-decorator': 'FormItem',
      'x-component': 'TextArea',
      'x-component-props': { rows: 2, maxlength: 160 },
    },
    domesticSeoKeywords: {
      type: 'string',
      title: '百度关键词（中文）',
      'x-decorator': 'FormItem',
      'x-component': 'Input',
    },
    russianPageTitle: {
      type: 'string',
      title: 'Yandex 搜索标题（俄语）',
      description: '俄罗斯市场主搜索；示例：Производитель минеральной ваты',
      'x-decorator': 'FormItem',
      'x-component': 'Input',
      'x-component-props': { placeholder: 'Производитель теплоизоляции · поставщик' },
    },
    russianSeoDescription: {
      type: 'string',
      title: 'Yandex 搜索简介（俄语）',
      'x-decorator': 'FormItem',
      'x-component': 'TextArea',
      'x-component-props': { rows: 2, maxlength: 160 },
    },
    russianSeoKeywords: {
      type: 'string',
      title: 'Yandex 关键词（俄语）',
      description: '如：минеральная вата, теплоизоляция, производитель',
      'x-decorator': 'FormItem',
      'x-component': 'Input',
    },
    allowIndex: {
      type: 'boolean',
      title: '允许搜索引擎收录',
      default: true,
      'x-decorator': 'FormItem',
      'x-component': 'Switch',
    },
  },
};
