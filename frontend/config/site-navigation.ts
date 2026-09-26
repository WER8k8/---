/** 站点主导航（顶栏与移动端抽屉共用） */
export interface SiteNavLink {
  /** i18n 键名，如 'nav.home' */
  label: string;
  to: string;
  /** i18n 键名，如 'nav.allCategories' */
  description?: string;
}

export interface SiteNavItem {
  /** i18n 键名，如 'nav.home' */
  label: string;
  /** 一级入口（含下拉时仍作为默认落地页） */
  to: string;
  children?: SiteNavLink[];
}

export const siteMainNavigation: SiteNavItem[] = [
  {
    label: 'nav.products',
    to: '/products',
    children: [
      { label: 'nav.productList', to: '/products', description: 'nav.allCategories' },
      { label: 'nav.finder', to: '/finder', description: 'nav.finderDesc' },
      { label: 'nav.compare', to: '/compare', description: 'nav.compareDesc' },
      { label: 'nav.calculators', to: '/calculators', description: 'nav.calculatorsDesc' },
    ],
  },
  {
    label: 'nav.solutions',
    to: '/solutions',
    children: [
      { label: 'nav.solOverview', to: '/solutions' },
      { label: 'nav.industries', to: '/industries', description: 'nav.industriesDesc' },
      { label: 'nav.projects', to: '/projects', description: 'nav.projectsDesc' },
      { label: 'nav.solExteriorWall', to: '/solutions/exterior-wall' },
      { label: 'nav.solRoof', to: '/solutions/roof' },
      { label: 'nav.solFloor', to: '/solutions/floor' },
      { label: 'nav.solIndustrial', to: '/solutions/industrial' },
      { label: 'nav.solWarehouse', to: '/solutions/warehouse' },
    ],
  },
  {
    label: 'nav.buyerPortal',
    to: '/orders',
    children: [
      { label: 'nav.orders', to: '/orders', description: 'nav.ordersDesc' },
      { label: 'nav.logistics', to: '/logistics', description: 'nav.logisticsDesc' },
      { label: 'nav.inquiries', to: '/inquiries', description: 'nav.inquiriesDesc' },
      { label: 'nav.procurement', to: '/procurement', description: 'nav.procurementDesc' },
      { label: 'nav.userCenter', to: '/user', description: 'nav.userCenterDesc' },
    ],
  },
  {
    label: 'nav.technical',
    to: '/technical',
    children: [
      { label: 'nav.technicalOverview', to: '/technical', description: 'nav.technicalOverviewDesc' },
      { label: 'nav.standards', to: '/standards', description: 'nav.standardsDesc' },
      { label: 'nav.resources', to: '/resources', description: 'nav.resourcesDesc' },
      { label: 'nav.calculator', to: '/calculator', description: 'nav.calculatorDesc' },
    ],
  },
  { label: 'nav.cases', to: '/cases' },
  { label: 'nav.markets', to: '/markets' },
  {
    label: 'nav.partner',
    to: '/distributor',
    children: [
      { label: 'nav.distributor', to: '/distributor', description: 'nav.distributorDesc' },
      { label: 'nav.oem', to: '/oem', description: 'nav.oemDesc' },
    ],
  },
  {
    label: 'nav.about',
    to: '/about',
    children: [
      { label: 'nav.companyIntro', to: '/about' },
      { label: 'nav.factory', to: '/factory', description: 'nav.factoryDesc' },
      { label: 'nav.quality', to: '/quality', description: 'nav.qualityDesc' },
      { label: 'nav.certifications', to: '/certifications', description: 'nav.certificationsDesc' },
      { label: 'nav.news', to: '/news' },
      { label: 'nav.privacy', to: '/privacy' },
      { label: 'nav.terms', to: '/terms' },
    ],
  },
  { label: 'nav.contact', to: '/contact' },
];

export function navKey(item: SiteNavItem): string {
  return item.to;
}
