/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import type { SiteBuilderTemplateId } from './types';
import { layoutKind, layoutLabel } from './buildPageShell';

export interface TemplatePreviewColors {
  headerBg: string;
  heroBg: string;
  accent: string;
  primary: string;
  layout: 'classic' | 'hero-banner' | 'industrial';
  layoutLabel: string;
}

export const TEMPLATE_PREVIEW_COLORS: Record<SiteBuilderTemplateId, TemplatePreviewColors> = {
  'premium-b2b-v1': {
    headerBg: '#0c4a6e',
    heroBg: '#f0f9ff',
    accent: '#0284c7',
    primary: '#0c4a6e',
    layout: layoutKind('premium-b2b-v1'),
    layoutLabel: layoutLabel('premium-b2b-v1'),
  },
  'insulation-classic': {
    headerBg: '#1e293b',
    heroBg: '#f1f5f9',
    accent: '#4a9b8c',
    primary: '#1e3a5f',
    layout: layoutKind('insulation-classic'),
    layoutLabel: layoutLabel('insulation-classic'),
  },
  'building-modern': {
    headerBg: '#115e59',
    heroBg: '#ecfdf5',
    accent: '#14b8a6',
    primary: '#0f766e',
    layout: layoutKind('building-modern'),
    layoutLabel: layoutLabel('building-modern'),
  },
  'export-pro': {
    headerBg: '#1e40af',
    heroBg: '#eff6ff',
    accent: '#4a9b8c',
    primary: '#1d4ed8',
    layout: layoutKind('export-pro'),
    layoutLabel: layoutLabel('export-pro'),
  },
  'fireproof-safety': {
    headerBg: '#7f1d1d',
    heroBg: '#fef2f2',
    accent: '#dc2626',
    primary: '#991b1b',
    layout: layoutKind('fireproof-safety'),
    layoutLabel: layoutLabel('fireproof-safety'),
  },
  'rubber-insulation': {
    headerBg: '#166534',
    heroBg: '#f0fdf4',
    accent: '#16a34a',
    primary: '#14532d',
    layout: layoutKind('rubber-insulation'),
    layoutLabel: layoutLabel('rubber-insulation'),
  },
  'steel-structure': {
    headerBg: '#1e293b',
    heroBg: '#f8fafc',
    accent: '#64748b',
    primary: '#334155',
    layout: layoutKind('steel-structure'),
    layoutLabel: layoutLabel('steel-structure'),
  },
  'ceramic-stone': {
    headerBg: '#44403c',
    heroBg: '#fafaf9',
    accent: '#78716c',
    primary: '#57534e',
    layout: layoutKind('ceramic-stone'),
    layoutLabel: layoutLabel('ceramic-stone'),
  },
  'hvac-duct': {
    headerBg: '#075985',
    heroBg: '#f0f9ff',
    accent: '#0ea5e9',
    primary: '#0369a1',
    layout: layoutKind('hvac-duct'),
    layoutLabel: layoutLabel('hvac-duct'),
  },
};
