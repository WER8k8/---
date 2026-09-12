"""全球化多语言 Schema"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GlossaryTermCreate(BaseModel):
    zh: str
    en: str
    ja: Optional[str] = None
    ko: Optional[str] = None
    de: Optional[str] = None
    fr: Optional[str] = None
    es: Optional[str] = None
    pt: Optional[str] = None
    it: Optional[str] = None
    nl: Optional[str] = None
    ru: Optional[str] = None
    ar: Optional[str] = None
    tr: Optional[str] = None
    fa: Optional[str] = None
    he: Optional[str] = None
    th: Optional[str] = None
    vi: Optional[str] = None
    ms: Optional[str] = None
    hi: Optional[str] = None
    id: Optional[str] = None
    tl: Optional[str] = None
    bn: Optional[str] = None
    my: Optional[str] = None
    km: Optional[str] = None
    pl: Optional[str] = None
    cs: Optional[str] = None
    uk: Optional[str] = None
    sv: Optional[str] = None
    sw: Optional[str] = None
    ha: Optional[str] = None
    zu: Optional[str] = None
    am: Optional[str] = None
    category: str = "建材"


class GlossaryTermUpdate(BaseModel):
    zh: Optional[str] = None
    en: Optional[str] = None
    ja: Optional[str] = None
    ko: Optional[str] = None
    de: Optional[str] = None
    fr: Optional[str] = None
    es: Optional[str] = None
    pt: Optional[str] = None
    it: Optional[str] = None
    nl: Optional[str] = None
    ru: Optional[str] = None
    ar: Optional[str] = None
    tr: Optional[str] = None
    fa: Optional[str] = None
    he: Optional[str] = None
    th: Optional[str] = None
    vi: Optional[str] = None
    ms: Optional[str] = None
    hi: Optional[str] = None
    id: Optional[str] = None
    tl: Optional[str] = None
    bn: Optional[str] = None
    my: Optional[str] = None
    km: Optional[str] = None
    pl: Optional[str] = None
    cs: Optional[str] = None
    uk: Optional[str] = None
    sv: Optional[str] = None
    sw: Optional[str] = None
    ha: Optional[str] = None
    zu: Optional[str] = None
    am: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class GlossaryTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    zh: str
    en: str
    ja: Optional[str] = None
    ko: Optional[str] = None
    de: Optional[str] = None
    fr: Optional[str] = None
    es: Optional[str] = None
    pt: Optional[str] = None
    it: Optional[str] = None
    nl: Optional[str] = None
    ru: Optional[str] = None
    ar: Optional[str] = None
    tr: Optional[str] = None
    fa: Optional[str] = None
    he: Optional[str] = None
    th: Optional[str] = None
    vi: Optional[str] = None
    ms: Optional[str] = None
    hi: Optional[str] = None
    id: Optional[str] = None
    tl: Optional[str] = None
    bn: Optional[str] = None
    my: Optional[str] = None
    km: Optional[str] = None
    pl: Optional[str] = None
    cs: Optional[str] = None
    uk: Optional[str] = None
    sv: Optional[str] = None
    sw: Optional[str] = None
    ha: Optional[str] = None
    zu: Optional[str] = None
    am: Optional[str] = None
    category: str
    status: str
    created_at: datetime
    updated_at: datetime


class TranslationTaskCreate(BaseModel):
    name: str
    source_lang: str = "zh"
    target_lang: str


class TranslationTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    source_lang: str
    target_lang: str
    total_items: int
    completed_items: int
    status: str
    created_at: datetime


class TranslationRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_text: str
    translated_text: Optional[str] = None
    source_lang: str
    target_lang: str
    status: str
    rating: int
    created_at: datetime
