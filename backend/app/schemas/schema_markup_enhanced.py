from typing import Optional
from pydantic import BaseModel


class OrganizationSchema(BaseModel):
    name: str = "优丁建材有限公司"
    url: str = "https://www.youdingjiancai.com"
    logo: str = "https://www.youdingjiancai.com/images/logo.png"
    description: str = "专注新型建筑材料研发与生产20年，提供轻集料混凝土、陶粒混凝土、加气混凝土、保温砂浆等高品质产品"
    founding_date: str = "2006"
    telephone: str = "+86-400-888-8888"
    email: str = "info@youdingjiancai.com"
    address_country: str = "CN"
    address_region: str = "中国"

    def to_json_ld(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": self.name,
            "url": self.url,
            "logo": self.logo,
            "description": self.description,
            "foundingDate": self.founding_date,
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": self.telephone,
                "email": self.email,
                "contactType": "customer service",
                "availableLanguage": ["Chinese", "English"]
            },
            "address": {
                "@type": "PostalAddress",
                "addressCountry": self.address_country,
                "addressRegion": self.address_region
            },
            "sameAs": [self.url]
        }


class ProductSchema(BaseModel):
    name: str
    description: str
    url: str
    image: Optional[str] = None
    brand: str = "优丁建材"
    category: str = "建筑材料"
    material: Optional[str] = None
    density: Optional[str] = None
    compressive_strength: Optional[str] = None
    thermal_conductivity: Optional[str] = None

    def to_json_ld(self) -> dict:
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "brand": {
                "@type": "Brand",
                "name": self.brand
            },
            "category": self.category
        }
        if self.image:
            data["image"] = self.image
        if self.material:
            data["material"] = self.material
        if self.density:
            data["additionalProperty"] = [
                {"@type": "PropertyValue", "name": "密度", "value": self.density},
            ]
        if self.compressive_strength:
            if "additionalProperty" not in data:
                data["additionalProperty"] = []
            data["additionalProperty"].append(
                {"@type": "PropertyValue", "name": "抗压强度", "value": self.compressive_strength}
            )
        if self.thermal_conductivity:
            if "additionalProperty" not in data:
                data["additionalProperty"] = []
            data["additionalProperty"].append(
                {"@type": "PropertyValue", "name": "导热系数", "value": self.thermal_conductivity}
            )
        return data


class ArticleSchema(BaseModel):
    headline: str
    description: str
    url: str
    author: str = "优丁建材"
    publisher: str = "优丁建材有限公司"
    publisher_logo: str = "https://www.youdingjiancai.com/images/logo.png"
    date_published: str = ""
    date_modified: str = ""
    image: Optional[str] = None

    def to_json_ld(self) -> dict:
        data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": self.headline,
            "description": self.description,
            "url": self.url,
            "author": {
                "@type": "Organization",
                "name": self.author
            },
            "publisher": {
                "@type": "Organization",
                "name": self.publisher,
                "logo": {
                    "@type": "ImageObject",
                    "url": self.publisher_logo
                }
            }
        }
        if self.date_published:
            data["datePublished"] = self.date_published
        if self.date_modified:
            data["dateModified"] = self.date_modified
        if self.image:
            data["image"] = self.image
        return data


class BreadcrumbSchema(BaseModel):
    items: list[dict] = []

    def to_json_ld(self) -> dict:
        item_list = []
        for idx, item in enumerate(self.items, 1):
            item_list.append({
                "@type": "ListItem",
                "position": idx,
                "name": item.get("name", ""),
                "item": item.get("url", "")
            })
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": item_list
        }


class FAQSchema(BaseModel):
    questions: list[dict] = []

    def to_json_ld(self) -> dict:
        main_entities = []
        for qa in self.questions:
            main_entities.append({
                "@type": "Question",
                "name": qa.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa.get("answer", "")
                }
            })
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entities
        }


class LocalBusinessSchema(BaseModel):
    name: str = "优丁建材有限公司"
    telephone: str = "+86-400-888-8888"
    email: str = "info@youdingjiancai.com"
    url: str = "https://www.youdingjiancai.com"
    address_country: str = "CN"
    address_region: str = "中国"
    opening_hours: str = "Mo-Fr 08:00-18:00"
    price_range: str = "¥¥"

    def to_json_ld(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": self.name,
            "telephone": self.telephone,
            "email": self.email,
            "url": self.url,
            "address": {
                "@type": "PostalAddress",
                "addressCountry": self.address_country,
                "addressRegion": self.address_region
            },
            "openingHours": self.opening_hours,
            "priceRange": self.price_range
        }


def generate_combined_schema(schemas: list[dict]) -> str:
    import json
    return json.dumps(schemas, ensure_ascii=False, indent=2)
