# API 接口定义

## 1. 产品管理模块

### 1.1 产品列表
```http
GET /api/v1/products
Query: ?page=1&page_size=20&category_id={uuid}&keyword={string}
Response: {
  "total": 100,
  "items": [{
    "id": "uuid",
    "name": "产品名称",
    "slug": "product-slug",
    "category_id": "uuid",
    "density": 1200.00,
    "strength_grade": "LC20",
    "thermal_conductivity": 0.22,
    "description": "产品描述",
    "meta_title": "SEO标题",
    "meta_description": "SEO描述",
    "sort_order": 0,
    "is_published": true,
    "created_at": "2025-01-01T00:00:00Z"
  }],
  "page": 1,
  "page_size": 20
}
Error Codes: 400(参数错误), 500(服务器错误)
```

### 1.2 产品详情
```http
GET /api/v1/products/{slug}
Response: { ...产品完整信息... }
Error Codes: 404(产品不存在)
```

### 1.3 创建产品
```http
POST /api/v1/products
Body: {
  "name": "产品名称",
  "category_id": "uuid",
  "density": 1200.00,
  "strength_grade": "LC20",
  "thermal_conductivity": 0.22,
  "description": "产品描述",
  "meta_title": "SEO标题(可选)",
  "meta_description": "SEO描述(可选)",
  "is_published": false
}
Response: { ...创建后的产品信息... }
Error Codes: 400(验证失败), 409(slug冲突)
```

### 1.4 更新产品
```http
PUT /api/v1/products/{id}
Body: { ...需要更新的字段... }
Response: { ...更新后的产品信息... }
```

### 1.5 删除产品
```http
DELETE /api/v1/products/{id}
Response: { "message": "删除成功" }
Error Codes: 404(产品不存在)
```

## 2. 内容管理模块

### 2.1 内容页面列表
```http
GET /api/v1/pages
Query: ?page=1&page_size=20&page_type={string}
Response: { "total": 50, "items": [...], "page": 1 }
```

### 2.2 内容页面详情
```http
GET /api/v1/pages/{slug}
Response: { ...页面完整信息... }
```

### 2.3 创建页面
```http
POST /api/v1/pages
Body: {
  "title": "页面标题",
  "content": "页面内容(HTML)",
  "page_type": "about|news|contact|custom",
  "meta_title": "SEO标题(可选)",
  "meta_description": "SEO描述(可选)",
  "is_published": false
}
```

### 2.4 更新页面
```http
PUT /api/v1/pages/{id}
Body: { ...需要更新的字段... }
```

### 2.5 删除页面
```http
DELETE /api/v1/pages/{id}
```

## 3. SEO 管理模块

### 3.1 SEO 概览仪表盘
```http
GET /api/v1/seo/dashboard
Response: {
  "total_keywords": 150,
  "ranked_keywords": 120,
  "avg_rank": 8.5,
  "ai_optimized_pages": 45,
  "llms_txt_generated": true,
  "last_audit_score": 85,
  "keyword_trend": [{"date": "2025-01", "avg_rank": 12}, ...],
  "page_coverage": [{"type": "optimized", "count": 45}, ...]
}
```

### 3.2 页面 SEO 管理
```http
GET /api/v1/seo/pages
Query: ?page=1&page_size=20&search={string}&status={string}
Response: {
  "total": 100,
  "items": [{
    "id": "uuid",
    "title": "页面标题",
    "meta_title": "SEO标题",
    "meta_description": "SEO描述",
    "meta_keywords": "关键词",
    "ai_optimized": true,
    "optimized_at": "2025-01-01T00:00:00Z",
    "status": "optimized|pending|failed"
  }],
  "page": 1,
  "page_size": 20
}

PUT /api/v1/seo/pages/{id}
Body: {
  "meta_title": "新SEO标题",
  "meta_description": "新SEO描述",
  "meta_keywords": "新关键词"
}

POST /api/v1/seo/pages/{id}/optimize
Body: { "ai_model": "gpt-4o|claude-3-opus" }
Response: { ...AI优化后的内容... }
```

### 3.3 LLMs.txt 生成
```http
POST /api/v1/seo/generate-llms-txt
Body: {
  "business_type": "轻集料混凝土",
  "keywords": ["轻集料混凝土", "LC20", ...],
  "ai_model": "gpt-4o",
  "temperature": 0.3,
  "max_tokens": 2000
}
Response: {
  "content": "# llms.txt\n# 网站: https://youding.com\n...",
  "version": "1.0.0",
  "token_usage": 1500,
  "cost": 0.03
}

POST /api/v1/seo/validate-llms-txt
Body: { "content": "llms.txt内容" }
Response: {
  "is_valid": true,
  "issues": [],
  "suggestions": []
}
```

### 3.4 AI 内容优化
```http
POST /api/v1/seo/optimize-content
Body: {
  "content": "原始内容",
  "optimization_type": "title|description|alt_text|content",
  "keywords": ["核心关键词", "长尾关键词"],
  "ai_model": "gpt-4o"
}
Response: {
  "optimized_content": "优化后的内容",
  "changes": ["修改点1", "修改点2"],
  "token_usage": 800,
  "cost": 0.02,
  "technical_params_preserved": true
}
```

### 3.5 网站审计
```http
POST /api/v1/seo/audit
Body: { "url": "https://youding.com", "audit_type": "full|quick" }
Response: {
  "audit_id": "uuid",
  "status": "running|completed|failed"
}

GET /api/v1/seo/audit/{id}
Response: {
  "id": "uuid",
  "url": "https://youding.com",
  "score": 85,
  "issues": [
    {"category": "技术合规", "severity": "high|medium|low", "description": "...", "recommendation": "..."}
  ],
  "recommendations": [
    {"priority": 1, "action": "修复...", "effort": "low|medium|high", "impact": "high"}
  ],
  "completed_at": "2025-01-01T00:00:00Z"
}
```

### 3.6 Schema 标记管理
```http
POST /api/v1/seo/schema
Body: {
  "resource_type": "product|page",
  "resource_id": "uuid",
  "schema_type": "Product|Article|BreadcrumbList|FAQPage|Organization"
}
Response: {
  "schema_markup": { "@context": "https://schema.org", "@type": "Product", ... }
}

PUT /api/v1/seo/schema/{id}
Body: { "schema_markup": { ...自定义JSON-LD... } }
```

## 4. AI 配置模块

### 4.1 AI 模型配置
```http
GET /api/v1/system/ai-config
Response: {
  "available_models": ["gpt-4o", "claude-3-opus", "gemini-1.5-pro"],
  "default_model": "gpt-4o",
  "temperature": 0.3,
  "max_tokens": 2000,
  "monthly_budget": 100.00,
  "total_spent": 12.50
}

PUT /api/v1/system/ai-config
Body: {
  "default_model": "gpt-4o",
  "temperature": 0.3,
  "max_tokens": 2000,
  "monthly_budget": 100.00
}
```

## 5. 系统管理模块

### 5.1 用户认证
```http
POST /api/v1/auth/login
Body: { "username": "admin", "password": "***" }
Response: { "access_token": "jwt_token", "token_type": "bearer", "expires_in": 3600 }

POST /api/v1/auth/refresh
Header: Authorization: Bearer {token}
Response: { "access_token": "new_jwt_token" }
```

### 5.2 用户管理
```http
GET /api/v1/system/users
Response: { ...用户列表... }

POST /api/v1/system/users
Body: { "username": "...", "email": "...", "password": "...", "role": "admin|editor|viewer" }

PUT /api/v1/system/users/{id}
DELETE /api/v1/system/users/{id}
```

### 5.3 操作日志
```http
GET /api/v1/system/logs
Query: ?page=1&page_size=20&user_id={uuid}&action={string}&start_date={date}&end_date={date}
Response: {
  "total": 1000,
  "items": [{
    "id": "uuid",
    "user_id": "uuid",
    "username": "admin",
    "action": "UPDATE_PRODUCT",
    "resource_type": "product",
    "resource_id": "uuid",
    "details": { "changed_fields": ["name", "density"] },
    "ip_address": "192.168.1.1",
    "created_at": "2025-01-01T00:00:00Z"
  }]
}
```

## 通用错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| UNAUTHORIZED | 401 | 未认证或token过期 |
| FORBIDDEN | 403 | 无权限访问 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突(如slug重复) |
| RATE_LIMITED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| AI_SERVICE_ERROR | 502 | AI服务调用失败 |
