import json
from typing import Dict, Any, List, Optional
from app.models.schema_markup import SchemaTemplate


class SchemaGenerator:
    """Schema标记生成器服务"""
    
    SUPPORTED_SCHEMA_TYPES = [
        "Organization",
        "Product",
        "Article",
        "WebPage",
        "BreadcrumbList",
        "FAQPage",
        "HowTo",
        "LocalBusiness",
        "Review",
        "AggregateRating",
    ]
    
    def __init__(self):
        pass
    
    def generate_schema(self, schema_type: str, data: Dict[str, Any], include_context: bool = True) -> Dict[str, Any]:
        """
        生成指定类型的Schema标记
        
        Args:
            schema_type: Schema类型
            data: 业务数据
            include_context: 是否包含上下文信息
        
        Returns:
            完整的Schema标记字典
        """
        if schema_type not in self.SUPPORTED_SCHEMA_TYPES:
            raise ValueError(f"不支持的Schema类型: {schema_type}")
        
        generator_method = getattr(self, f"_generate_{schema_type.lower()}", None)
        if not generator_method:
            raise ValueError(f"未实现的Schema类型: {schema_type}")
        
        return generator_method(data, include_context)
    
    def _generate_organization(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成Organization Schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": data.get("name", "优丁建材有限公司"),
            "legalName": data.get("legal_name", data.get("name", "优丁建材有限公司")),
            "description": data.get("description", "专业轻集料混凝土生产商"),
            "url": data.get("url", "https://www.youdingjiancai.com"),
            "logo": data.get("logo", "https://www.youdingjiancai.com/logo.png"),
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": data.get("phone", ""),
                "contactType": "customer service"
            },
            "address": {
                "@type": "PostalAddress",
                "streetAddress": data.get("address", ""),
                "addressLocality": data.get("city", ""),
                "addressRegion": data.get("region", ""),
                "postalCode": data.get("postal_code", ""),
                "addressCountry": "CN"
            },
            "foundingDate": data.get("founding_date", "2010"),
            "numberOfEmployees": data.get("employee_count", "100-200"),
        }
        
        if include_context:
            schema["sameAs"] = data.get("social_links", [
                "https://www.weixin.com/youding",
                "https://www.linkedin.com/company/youding"
            ])
        
        return schema
    
    def _generate_product(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成Product Schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "brand": {
                "@type": "Brand",
                "name": data.get("brand", "优丁建材")
            },
            "sku": data.get("sku", ""),
            "mpn": data.get("mpn", ""),
            "image": data.get("image", ""),
            "url": data.get("url", ""),
            "category": data.get("category", "建筑材料"),
            "material": data.get("material", "轻集料混凝土"),
            "weight": {
                "@type": "QuantitativeValue",
                "value": data.get("weight_value", "25"),
                "unitCode": "KG"
            },
            "offers": {
                "@type": "Offer",
                "price": data.get("price", "0"),
                "priceCurrency": "CNY",
                "availability": data.get("availability", "https://schema.org/InStock"),
                "seller": {
                    "@type": "Organization",
                    "name": "优丁建材有限公司"
                }
            }
        }
        
        if data.get("rating"):
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": data.get("rating", "4.5"),
                "reviewCount": data.get("review_count", "100")
            }
        
        if include_context and data.get("specifications"):
            schema["additionalProperty"] = []
            for key, value in data["specifications"].items():
                schema["additionalProperty"].append({
                    "@type": "PropertyValue",
                    "name": key,
                    "value": value
                })
        
        return schema
    
    def _generate_article(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成Article Schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": data.get("headline", ""),
            "description": data.get("description", ""),
            "articleBody": data.get("content", ""),
            "author": {
                "@type": "Person",
                "name": data.get("author_name", "优丁技术团队"),
                "url": data.get("author_url", "")
            },
            "publisher": {
                "@type": "Organization",
                "name": "优丁建材有限公司",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://www.youdingjiancai.com/logo.png"
                }
            },
            "datePublished": data.get("published_date", ""),
            "dateModified": data.get("modified_date", ""),
            "image": data.get("image", ""),
            "keywords": data.get("keywords", []),
            "wordCount": len(data.get("content", "").split())
        }
        
        if include_context and data.get("category"):
            schema["articleSection"] = data["category"]
        
        return schema
    
    def _generate_webpage(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成WebPage Schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "url": data.get("url", ""),
            "inLanguage": "zh-CN",
            "isPartOf": {
                "@type": "WebSite",
                "name": data.get("site_name", "优丁建材官网"),
                "url": data.get("site_url", "https://www.youdingjiancai.com")
            }
        }
        
        if include_context and data.get("breadcrumb"):
            schema["breadcrumb"] = self._generate_breadcrumb({"items": data["breadcrumb"]}, False)
        
        return schema
    
    def _generate_breadcrumblist(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成BreadcrumbList Schema"""
        items = data.get("items", [])
        breadcrumb_items = []
        
        for i, item in enumerate(items, 1):
            breadcrumb_items.append({
                "@type": "ListItem",
                "position": i,
                "name": item.get("name", ""),
                "item": item.get("url", "")
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumb_items
        }
    
    def _generate_faqpage(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成FAQPage Schema"""
        questions = data.get("questions", [])
        faq_items = []
        
        for q in questions:
            faq_items.append({
                "@type": "Question",
                "name": q.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": q.get("answer", "")
                }
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_items
        }
    
    def _generate_howto(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成HowTo Schema"""
        steps = data.get("steps", [])
        howto_steps = []
        
        for i, step in enumerate(steps, 1):
            howto_steps.append({
                "@type": "HowToStep",
                "position": i,
                "name": step.get("name", f"步骤{i}"),
                "text": step.get("text", "")
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "step": howto_steps,
            "totalTime": data.get("total_time", "PT1H")
        }
    
    def _generate_localbusiness(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成LocalBusiness Schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": data.get("name", "优丁建材"),
            "description": data.get("description", "专业轻集料混凝土生产销售"),
            "image": data.get("image", ""),
            "telephone": data.get("phone", ""),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": data.get("address", ""),
                "addressLocality": data.get("city", ""),
                "addressRegion": data.get("region", ""),
                "postalCode": data.get("postal_code", ""),
                "addressCountry": "CN"
            },
            "openingHours": data.get("opening_hours", ["Mo-Sa 08:00-18:00"]),
            "url": data.get("url", "https://www.youdingjiancai.com")
        }
        
        return schema
    
    def _generate_review(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成Review Schema"""
        return {
            "@context": "https://schema.org",
            "@type": "Review",
            "reviewBody": data.get("body", ""),
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": data.get("rating", "5"),
                "bestRating": "5"
            },
            "author": {
                "@type": "Person",
                "name": data.get("author_name", "")
            },
            "itemReviewed": {
                "@type": "Product",
                "name": data.get("product_name", "")
            },
            "datePublished": data.get("published_date", "")
        }
    
    def _generate_aggregaterating(self, data: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """生成AggregateRating Schema"""
        return {
            "@context": "https://schema.org",
            "@type": "AggregateRating",
            "ratingValue": data.get("rating", "4.5"),
            "reviewCount": data.get("review_count", "100"),
            "bestRating": "5",
            "worstRating": "1"
        }
    
    def validate_schema(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证Schema标记的有效性
        
        Args:
            content: Schema内容
        
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        schema_type = None
        
        # 基本验证
        if "@context" not in content:
            errors.append({"code": "missing_context", "message": "缺少@context字段"})
        elif content["@context"] != "https://schema.org":
            warnings.append({"code": "invalid_context", "message": "@context建议使用https://schema.org"})
        
        if "@type" not in content:
            errors.append({"code": "missing_type", "message": "缺少@type字段"})
        else:
            schema_type = content["@type"]
            if schema_type not in self.SUPPORTED_SCHEMA_TYPES:
                warnings.append({"code": "unsupported_type", "message": f"不支持的Schema类型: {schema_type}"})
        
        # 特定类型验证
        if schema_type == "Product":
            if not content.get("name"):
                errors.append({"code": "product_missing_name", "message": "Product缺少name字段"})
        
        if schema_type == "Article":
            if not content.get("headline"):
                errors.append({"code": "article_missing_headline", "message": "Article缺少headline字段"})
            if not content.get("articleBody"):
                errors.append({"code": "article_missing_body", "message": "Article缺少articleBody字段"})
        
        if schema_type == "Organization":
            if not content.get("name"):
                errors.append({"code": "org_missing_name", "message": "Organization缺少name字段"})
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "schema_type": schema_type
        }
    
    def get_schema_types(self) -> List[str]:
        """获取支持的Schema类型列表"""
        return self.SUPPORTED_SCHEMA_TYPES
    
    def get_schema_template(self, schema_type: str) -> Dict[str, Any]:
        """获取指定类型的Schema模板"""
        templates = {
            "Organization": {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "",
                "description": "",
                "url": "",
                "logo": "",
                "contactPoint": {
                    "@type": "ContactPoint",
                    "telephone": "",
                    "contactType": "customer service"
                },
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "",
                    "addressLocality": "",
                    "addressRegion": "",
                    "postalCode": "",
                    "addressCountry": "CN"
                }
            },
            "Product": {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": "",
                "description": "",
                "brand": {"@type": "Brand", "name": ""},
                "sku": "",
                "image": "",
                "url": "",
                "offers": {
                    "@type": "Offer",
                    "price": "",
                    "priceCurrency": "CNY",
                    "availability": "https://schema.org/InStock"
                }
            },
            "Article": {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "",
                "description": "",
                "articleBody": "",
                "author": {"@type": "Person", "name": ""},
                "publisher": {
                    "@type": "Organization",
                    "name": "",
                    "logo": {"@type": "ImageObject", "url": ""}
                },
                "datePublished": "",
                "dateModified": "",
                "image": "",
                "keywords": []
            },
            "FAQPage": {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": []
            },
            "BreadcrumbList": {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": []
            }
        }
        
        return templates.get(schema_type, {})
    
    def convert_to_json_ld(self, content: Dict[str, Any]) -> str:
        """将Schema字典转换为JSON-LD字符串"""
        return json.dumps(content, ensure_ascii=False, indent=2)
