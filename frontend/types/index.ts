export interface Product {
  id: string
  name: string
  subtitle?: string
  description?: string
  price?: number
  images?: string[]
  category?: string
  categoryId?: string
  categoryName?: string
  rating?: number
  reviewCount?: number
  stock?: number
  tags?: string[]
  specifications?: Record<string, string>
  isActive?: boolean
  slug?: string
  createdAt?: string
  updatedAt?: string
}

export interface ProductCategory {
  id: string
  name: string
  description?: string
  icon?: string
  sortOrder?: number
  isActive?: boolean
  slug?: string
  productCount?: number
}

export interface Case {
  id: string
  title: string
  description?: string
  category?: string
  images?: string[]
  beforeImages?: string[]
  afterImages?: string[]
  projectValue?: number
  duration?: string
  location?: string
  completionDate?: string
  challenges?: string
  solutions?: string
  results?: string
  isActive?: boolean
  slug?: string
  createdAt?: string
  updatedAt?: string
}

export interface News {
  id: string
  title: string
  summary?: string
  content?: string
  coverImage?: string
  category?: string
  author?: string
  publishDate?: string
  viewCount?: number
  isActive?: boolean
  slug?: string
  tags?: string[]
  seoTitle?: string
  seoDescription?: string
  seoKeywords?: string
}

export interface Inquiry {
  id: string
  name: string
  phone: string
  email?: string
  company?: string
  message: string
  productInterest?: string
  status: 'pending' | 'contacted' | 'converted' | 'closed'
  createdAt: string
  updatedAt?: string
  notes?: string
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
  avatar?: string
  isActive: boolean
  lastLoginAt?: string
  createdAt: string
}

export interface SeoConfig {
  id: string
  pagePath: string
  title?: string
  description?: string
  keywords?: string
  ogImage?: string
  canonicalUrl?: string
  schemaMarkup?: string
  updatedAt: string
}

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PageResponse<T = any> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}
