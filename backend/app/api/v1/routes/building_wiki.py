"""AI建材百科路由 - 建材行业知识文章生成与管理"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/building-wiki"
ROUTE_TAGS = ["建材Wiki知识库"]

router = APIRouter()

# ========== 内置种子文章（预设5篇建材百科文章） ==========
SEED_ARTICLES = [
    {
        "id": "seed_1",
        "keyword": "轻集料混凝土",
        "title": "轻集料混凝土的特点与应用全解析",
        "content": """轻集料混凝土是一种以轻质骨料替代普通砂石的新型混凝土材料，其干表观密度通常为800～1900kg/m³，远低于普通混凝土的2400kg/m³。常用的轻集料包括陶粒、浮石、膨胀珍珠岩、炉渣等。

轻集料混凝土的核心优势在于减重。在高层建筑中，采用轻集料混凝土浇筑楼板或填充墙，可降低结构自重15%～30%，从而减少地基荷载和梁柱截面，节省钢筋用量。同时，轻集料内部的多孔结构赋予了材料良好的保温隔热性能，导热系数仅为普通混凝土的1/3～1/2，是建筑节能的优选方案。

在施工方面，轻集料混凝土的流动性稍低于普通混凝土，泵送距离受限，施工前需对轻集料进行预湿处理，防止搅拌过程中骨料吸水影响水灰比。拆模时间通常比普通混凝土晚1～2天，但整体施工周期影响不大。

值得注意的是，轻集料混凝土的弹性模量较低，抗裂性能优于普通混凝土，配合适当的结构设计，可有效减少温度裂缝的产生。目前，轻集料混凝土已广泛应用于桥梁桥面铺装、大跨度屋面板、节能外墙板等场景。""",
        "style": "科普风",
        "status": "published",
        "published_at": "2026-05-19 10:30:00",
        "views": 328,
    },
    {
        "id": "seed_2",
        "keyword": "陶粒混凝土",
        "title": "陶粒混凝土：轻质高强的建筑新材料",
        "content": """陶粒混凝土是以陶粒为粗骨料的轻集料混凝土，因其密度低、强度高、保温好而备受工程界关注。

陶粒是以黏土、页岩或粉煤灰为主要原料，经高温焙烧而成的球形轻质骨料，表面有一层坚硬陶质釉壳，内部呈蜂窝状多孔结构。正是这种结构赋予陶粒混凝土"外强内松"的独特性能：外表层坚硬耐久，内芯多孔轻质且保温隔热。

从性能参数来看，陶粒混凝土的干密度一般为1200～1800kg/m³，比普通混凝土轻约25%～35%；抗压强度可达C20～C40，完全满足一般结构构件的要求。其保温性能尤为突出，导热系数约0.3～0.6W/(m·K)，仅为普通混凝土的1/3。此外，陶粒混凝土的耐火极限可达3小时以上，远超普通混凝土。

在工程应用中，陶粒混凝土特别适合用于以下几类场景：一是高层建筑的填充墙和隔墙，减轻自重；二是屋面保温层兼找坡层，一材多用；三是桥梁铺装层，降低桥面恒载；四是预制轻质墙板、砌块等装配式构件。

需要注意的是，陶粒混凝土的收缩率比普通混凝土大15%～25%，因此在长墙、大跨度构件中应设置伸缩缝或配置抗裂钢筋。同时，陶粒的筒压强度是决定性指标，选用时需根据设计强度等级匹配相应级配的陶粒。""",
        "style": "技术篇",
        "status": "published",
        "published_at": "2026-05-18 14:00:00",
        "views": 256,
    },
    {
        "id": "seed_3",
        "keyword": "保温砂浆",
        "title": "保温砂浆选购指南与施工要点",
        "content": """保温砂浆是建筑节能工程中应用最广泛的墙体保温材料之一，主要分为无机保温砂浆和有机保温砂浆两大类。

无机保温砂浆以膨胀珍珠岩、玻化微珠、硅藻土等为轻质骨料，配以水泥基胶凝材料和外加剂，具有防火等级A级、耐老化、与基层粘结牢固等突出优点。常见的无机保温砂浆干密度约300～500kg/m³，导热系数0.07～0.12W/(m·K)。有机保温砂浆以聚苯颗粒、废聚氨酯颗粒等为轻骨料，保温性能更优（导热系数0.05～0.08W/(m·K)），但防火等级仅为B1级。

选购保温砂浆时需关注三个关键指标：一是导热系数，越低保温效果越好；二是干密度，关系到墙体荷载；三是抗压强度，影响后续饰面施工的安全性。建议优先选择具备型式检验报告的正规品牌产品。

施工方面，保温砂浆的要点包括：基层必须清理干净并充分润湿；砂浆需严格按水灰比搅拌，静置5分钟后再二次搅拌使用；分层施工时每层厚度不宜超过20mm，待前一层表干后方可进行下一层；施工完成后应养护至少7天，期间避免暴晒和冻害。

常见问题中，保温砂浆最容易出现空鼓和开裂。空鼓原因通常是基层处理不当或一次抹灰过厚；开裂则多由材料收缩率大或养护不到位引起。解决方案是严格控制施工工艺，并在表面压入耐碱玻纤网格布以提高抗裂性。""",
        "style": "选购指南",
        "status": "published",
        "published_at": "2026-05-17 09:15:00",
        "views": 189,
    },
    {
        "id": "seed_4",
        "keyword": "加气砖",
        "title": "加气砖（蒸压加气混凝土砌块）全面介绍",
        "content": """加气砖，规范名称为蒸压加气混凝土砌块（AAC砌块），是以硅质材料（砂、粉煤灰）和钙质材料（石灰、水泥）为主要原料，加入铝粉发气剂，经配料、搅拌、浇注、预养、切割、蒸压养护而成的新型轻质墙体材料。

加气砖最突出的特点是"集轻质、保温、防火于一身"。其干密度仅500～700kg/m³，约为普通黏土砖的1/3、混凝土的1/4，可有效减轻建筑自重，降低基础和结构造价。导热系数0.11～0.18W/(m·K)，保温性能是普通黏土砖的4～5倍，240mm厚的加气砖墙体即可达到国家建筑节能65%的要求。耐火极限超过4小时，属于A级不燃材料。

在实际施工中，加气砖的加工性能极佳——可钉、可锯、可刨、可钻孔，大大方便了水电管线埋设和门窗安装。砌筑时采用专用粘结砂浆，灰缝仅3～5mm（传统砌筑灰缝10～15mm），减少了热桥效应。

使用加气砖时需注意以下几点：一是砌筑前应提前2天在砌块表面淋水（或采用专用界面剂），防止砌块过快吸收砂浆水分；二是砌筑完成后不宜立即抹灰，至少应间隔15天以上，待墙体沉降稳定后再进行；三是抹灰前应满挂钢丝网或耐碱玻纤网，防止裂缝产生；四是厨卫等潮湿房间底部应做C20素混凝土导墙（高度不低于200mm）。

加气砖的强度等级通常为A3.5～A5.0（Mpa），承载力不如普通混凝土，因此不适用于承重结构，主要用于框架结构的填充墙、隔墙及非承重外墙。""",
        "style": "技术篇",
        "status": "published",
        "published_at": "2026-05-16 16:45:00",
        "views": 412,
    },
    {
        "id": "seed_5",
        "keyword": "干混砂浆",
        "title": "干混砂浆与现场搅拌砂浆的全面对比",
        "content": """干混砂浆是将水泥、砂、矿物掺合料和外加剂按一定配比在工厂干拌均匀后，以袋装或散装形式运至施工现场，加水搅拌即可使用的砂浆产品。与之对应的是传统的现场搅拌砂浆，即施工方在工地现场自行配比搅拌。

从质量稳定性来看，干混砂浆优势明显。工厂采用自动计量系统和强力搅拌设备，配比精度可达±1%，比人工搅拌的±5%～10%精准得多。每批次产品的强度、和易性、保水率等指标一致，不会出现"这一车稀那一车干"的问题。现场搅拌砂浆则高度依赖工人经验和责任心，质量波动较大。

在环保方面，干混砂浆采用封闭式生产和运输，施工现场不堆放任水泥和砂子，减少粉尘排放约80%以上。而现场搅拌往往产生大量粉尘、废水和噪音，是城市扬尘治理的重点管控对象。

施工性能上，干混砂浆的保水率可达88%以上（国标要求≥88%），开放时间2～4小时，一次施工厚度可在5～30mm范围内灵活调整。保水率高意味着水分不易被基层吸走，水泥水化更充分，粘结强度更高，空鼓率大幅降低。

成本方面，干混砂浆的单价（到工地价）通常比自拌砂浆高30～50元/吨，但综合计算材料损耗减少10%～15%、返工修补成本几乎为零、施工效率提高30%以上，总体使用成本反而更低。特别是对于大型项目和城市重点工程，干混砂浆已成为主流选择。

近年来，国家住建部明确要求地级及以上城市全面推广使用预拌砂浆（含干混砂浆），禁止施工现场搅拌砂浆。可以预见，干混砂浆将全面取代现场搅拌砂浆，成为建筑砂浆市场的主流产品。""",
        "style": "对比分析",
        "status": "published",
        "published_at": "2026-05-15 11:30:00",
        "views": 174,
    },
]

# 运行时文章存储（种子文章 + 新生成的文章）
_articles = {a["id"]: a for a in SEED_ARTICLES}
_next_id = 6


class GenerateRequest(BaseModel):
    keyword: str
    style: str = "科普风"


class UpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    style: Optional[str] = None


@router.post("/generate")
async def generate_article(
    body: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 生成建材百科文章（内置种子 + 场景模型兜底）。"""
    from app.services.ai_invocation_service import invoke_llm
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    from app.services.tenant_product_profile_service import (
        ProductProfileRequiredError,
        require_product_profile_for_content,
    )
    global _next_id
    keyword = body.keyword.strip()
    if not keyword:
        return error_response(400, "关键词不能为空")

    tenant_id = resolve_tenant_id_for_user(db, current_user)
    if tenant_id:
        try:
            require_product_profile_for_content(db, str(tenant_id))
        except ProductProfileRequiredError as exc:
            return error_response(400, str(exc))

    style = body.style.strip() or "科普风"
    for art in _articles.values():
        if art["keyword"] == keyword:
            return error_response(409, f"关键词'{keyword}'的文章已存在")

    article = _generate_article_for_keyword(keyword, style)
    if article:
        art_id = f"seed_{_next_id}"
        _next_id += 1
        article["id"] = art_id
        article["keyword"] = keyword
        article["style"] = style
        article["status"] = "draft"
        article["published_at"] = None
        article["views"] = 0
        _articles[art_id] = article
        article["generation_mode"] = "preset_template"
        return success_response(
            data=article,
            message="文章生成成功（内置模板，非 LLM 实时生成）",
        )

    prompt = (
        f"请撰写一篇关于「{keyword}」的建材行业百科文章，风格：{style}。"
        "要求：结构含引言、性能特点、应用场景、注意事项，800～1200 字，客观专业。"
    )
    try:
        result = await invoke_llm(
            db,
            prompt=prompt,
            scenario="article",
            task_type="wiki:generate",
            max_tokens=2500,
            tenant_id=resolve_tenant_id_for_user(db, current_user),
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))

    content = (result.get("content") or "").strip()
    if not content:
        return error_response(502, "AI 未返回文章内容")

    art_id = f"seed_{_next_id}"
    _next_id += 1
    article = {
        "id": art_id,
        "keyword": keyword,
        "title": f"{keyword}：行业知识与应用指南",
        "content": content,
        "style": style,
        "status": "draft",
        "published_at": None,
        "views": 0,
        "scenario": result.get("scenario", "article"),
    }
    _articles[art_id] = article
    return success_response(data=article, message="文章生成成功")


@router.get("/articles")
async def list_articles(status: Optional[str] = Query(None),
                  page: int = Query(1, ge=1),
                  page_size: int = Query(20, ge=1, le=100),
                  current_user: User = Depends(get_current_user)):
    """已生成的文章列表"""
    items = list(_articles.values())
    if status:
        items = [a for a in items if a["status"] == status]

    items.sort(key=lambda a: a.get("published_at") or "", reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    return success_response(
        data={"items": page_items, "total": total, "page": page, "page_size": page_size},
        message="success",
    )


@router.get("/articles/{article_id}")
def get_article(article_id: str,
                current_user: User = Depends(get_current_user)):
    """获取单篇文章详情"""
    article = _articles.get(article_id)
    if not article:
        return error_response(404, "文章不存在")
    return success_response(data=article, message="success")


@router.put("/articles/{article_id}")
def update_article(article_id: str,
                   body: UpdateRequest,
                   current_user: User = Depends(get_current_user)):
    """编辑文章"""
    article = _articles.get(article_id)
    if not article:
        return error_response(404, "文章不存在")

    if body.title is not None:
        article["title"] = body.title
    if body.content is not None:
        article["content"] = body.content
    if body.style is not None:
        article["style"] = body.style

    return success_response(data=article, message="保存成功")


@router.post("/publish/{article_id}")
def publish_article(article_id: str,
                    current_user: User = Depends(get_current_user)):
    """发布文章到网站"""
    article = _articles.get(article_id)
    if not article:
        return error_response(404, "文章不存在")

    article["status"] = "published"
    article["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return success_response(data=article, message="发布成功")


@router.post("/unpublish/{article_id}")
def unpublish_article(article_id: str,
                      current_user: User = Depends(get_current_user)):
    """下架文章"""
    article = _articles.get(article_id)
    if not article:
        return error_response(404, "文章不存在")

    article["status"] = "draft"
    article["published_at"] = None
    return success_response(data=article, message="已下架")


@router.delete("/articles/{article_id}")
def delete_article(article_id: str,
                   current_user: User = Depends(get_current_user)):
    """删除文章"""
    if article_id not in _articles:
        return error_response(404, "文章不存在")

    del _articles[article_id]
    return success_response(message="删除成功")


def _generate_article_for_keyword(keyword: str, style: str) -> Optional[dict]:
    """根据关键词匹配内置种子文章（preset_template，非 LLM 实时生成）。"""
    keyword_map = {
        "轻集料混凝土": {
            "title": f"{keyword}的特点与应用全解析",
            "content": """轻集料混凝土是一种以轻质骨料替代普通砂石的新型混凝土材料，其干表观密度通常为800～1900kg/m³，远低于普通混凝土的2400kg/m³。常用的轻集料包括陶粒、浮石、膨胀珍珠岩、炉渣等。

轻集料混凝土的核心优势在于减重。在高层建筑中，采用轻集料混凝土浇筑楼板或填充墙，可降低结构自重15%～30%，从而减少地基荷载和梁柱截面，节省钢筋用量。同时，轻集料内部的多孔结构赋予了材料良好的保温隔热性能，导热系数仅为普通混凝土的1/3～1/2，是建筑节能的优选方案。

在施工方面，轻集料混凝土的流动性稍低于普通混凝土，泵送距离受限，施工前需对轻集料进行预湿处理，防止搅拌过程中骨料吸水影响水灰比。拆模时间通常比普通混凝土晚1～2天，但整体施工周期影响不大。

值得注意的是，轻集料混凝土的弹性模量较低，抗裂性能优于普通混凝土，配合适当的结构设计，可有效减少温度裂缝的产生。目前，轻集料混凝土已广泛应用于桥梁桥面铺装、大跨度屋面板、节能外墙板等场景。""",
        },
        "陶粒混凝土": {
            "title": f"{keyword}：轻质高强的建筑新材料",
            "content": """陶粒混凝土是以陶粒为粗骨料的轻集料混凝土，因其密度低、强度高、保温好而备受工程界关注。

陶粒是以黏土、页岩或粉煤灰为主要原料，经高温焙烧而成的球形轻质骨料，表面有一层坚硬陶质釉壳，内部呈蜂窝状多孔结构。正是这种结构赋予陶粒混凝土"外强内松"的独特性能：外表层坚硬耐久，内芯多孔轻质且保温隔热。

从性能参数来看，陶粒混凝土的干密度一般为1200～1800kg/m³，比普通混凝土轻约25%～35%；抗压强度可达C20～C40，完全满足一般结构构件的要求。其保温性能尤为突出，导热系数约0.3～0.6W/(m·K)，仅为普通混凝土的1/3。此外，陶粒混凝土的耐火极限可达3小时以上，远超普通混凝土。

在工程应用中，陶粒混凝土特别适合用于以下几类场景：一是高层建筑的填充墙和隔墙，减轻自重；二是屋面保温层兼找坡层，一材多用；三是桥梁铺装层，降低桥面恒载；四是预制轻质墙板、砌块等装配式构件。

需要注意的是，陶粒混凝土的收缩率比普通混凝土大15%～25%，因此在长墙、大跨度构件中应设置伸缩缝或配置抗裂钢筋。""",
        },
        "保温砂浆": {
            "title": f"{keyword}选购指南与施工要点",
            "content": """保温砂浆是建筑节能工程中应用最广泛的墙体保温材料之一，主要分为无机保温砂浆和有机保温砂浆两大类。

无机保温砂浆以膨胀珍珠岩、玻化微珠、硅藻土等为轻质骨料，配以水泥基胶凝材料和外加剂，具有防火等级A级、耐老化、与基层粘结牢固等突出优点。常见的无机保温砂浆干密度约300～500kg/m³，导热系数0.07～0.12W/(m·K)。有机保温砂浆以聚苯颗粒、废聚氨酯颗粒等为轻骨料，保温性能更优（导热系数0.05～0.08W/(m·K)），但防火等级仅为B1级。

选购保温砂浆时需关注三个关键指标：一是导热系数，越低保温效果越好；二是干密度，关系到墙体荷载；三是抗压强度，影响后续饰面施工的安全性。建议优先选择具备型式检验报告的正规品牌产品。

施工方面，保温砂浆的要点包括：基层必须清理干净并充分润湿；砂浆需严格按水灰比搅拌，静置5分钟后再二次搅拌使用；分层施工时每层厚度不宜超过20mm，待前一层表干后方可进行下一层；施工完成后应养护至少7天，期间避免暴晒和冻害。""",
        },
        "加气砖": {
            "title": f"{keyword}（蒸压加气混凝土砌块）全面介绍",
            "content": """加气砖，规范名称为蒸压加气混凝土砌块（AAC砌块），是以硅质材料（砂、粉煤灰）和钙质材料（石灰、水泥）为主要原料，加入铝粉发气剂，经配料、搅拌、浇注、预养、切割、蒸压养护而成的新型轻质墙体材料。

加气砖最突出的特点是"集轻质、保温、防火于一身"。其干密度仅500～700kg/m³，约为普通黏土砖的1/3、混凝土的1/4，可有效减轻建筑自重，降低基础和结构造价。导热系数0.11～0.18W/(m·K)，保温性能是普通黏土砖的4～5倍，240mm厚的加气砖墙体即可达到国家建筑节能65%的要求。耐火极限超过4小时，属于A级不燃材料。

在实际施工中，加气砖的加工性能极佳——可钉、可锯、可刨、可钻孔，大大方便了水电管线埋设和门窗安装。砌筑时采用专用粘结砂浆，灰缝仅3～5mm（传统砌筑灰缝10～15mm），减少了热桥效应。

使用加气砖时需注意以下几点：一是砌筑前应提前2天在砌块表面淋水（或采用专用界面剂），防止砌块过快吸收砂浆水分；二是砌筑完成后不宜立即抹灰，至少应间隔15天以上，待墙体沉降稳定后再进行；三是抹灰前应满挂钢丝网或耐碱玻纤网，防止裂缝产生。""",
        },
        "干混砂浆": {
            "title": f"{keyword}与现场搅拌砂浆的全面对比",
            "content": """干混砂浆是将水泥、砂、矿物掺合料和外加剂按一定配比在工厂干拌均匀后，以袋装或散装形式运至施工现场，加水搅拌即可使用的砂浆产品。与之对应的是传统的现场搅拌砂浆。

从质量稳定性来看，干混砂浆优势明显。工厂采用自动计量系统和强力搅拌设备，配比精度可达±1%，比人工搅拌的±5%～10%精准得多。每批次产品的强度、和易性、保水率等指标一致。

在环保方面，干混砂浆采用封闭式生产和运输，施工现场不堆放任水泥和砂子，减少粉尘排放约80%以上。

施工性能上，干混砂浆的保水率可达88%以上（国标要求≥88%），开放时间2～4小时，一次施工厚度可在5～30mm范围内灵活调整。保水率高意味着水分不易被基层吸走，水泥水化更充分，粘结强度更高，空鼓率大幅降低。

成本方面，干混砂浆的单价通常比自拌砂浆高30～50元/吨，但综合计算材料损耗减少10%～15%、返工修补成本几乎为零、施工效率提高30%以上，总体使用成本反而更低。近年来，国家住建部明确要求地级及以上城市全面推广使用预拌砂浆（含干混砂浆），禁止施工现场搅拌砂浆。""",
        },
        "岩棉板": {
            "title": f"{keyword}：A1防火与外墙保温应用要点",
            "content": """岩棉板是以玄武岩等天然岩石为主要原料，经高温熔融、纤维化、打褶加压、切割而成的无机纤维保温板材，属于 A1 级不燃材料，是大城、河间产业带出口量较大的保温主材之一。

从性能来看，岩棉板导热系数通常约 0.035～0.045 W/(m·K)，密度常见 80～140 kg/m³，耐火极限高，适用于建筑外墙外保温、屋面保温及防火隔离带。工程上常用厚度为 50 mm、75 mm、100 mm，具体需结合当地建筑节能与防火规范确定。

选购与验货时建议关注：① 容重与导热系数检测报告是否齐全；② 憎水率（外墙应用建议关注）；③ 尺寸偏差与板面平整度；④ 是否有完整出厂合格证与批次追溯。河北大城留各庄、河间束城等集群厂家较多，出口前须按目标国认证要求准备资料，勿夸大未获证指标。

施工方面，岩棉板需配套专用粘结砂浆与锚固件，粘贴面积、锚栓数量和网格布搭接应满足设计与图集要求。雨天、基层含水率过高时不宜施工；防火隔离带部位应使用专用锚固方案，避免热桥与空鼓。""",
        },
    }
    matched = keyword_map.get(keyword)
    if not matched:
        # 模糊匹配
        for k, v in keyword_map.items():
            if k in keyword or keyword in k:
                matched = v
                break

    if matched:
        return {
            "title": matched["title"],
            "content": matched["content"],
            "keyword": keyword,
            "style": style,
            "status": "draft",
            "published_at": None,
            "views": 0,
        }

    return None


def create_forum_qa_draft(question: str, answer: str) -> dict | None:
    """论坛采纳答案 → Wiki 草稿（未发布，须人工审核）。"""
    global _next_id
    q = (question or "").strip()
    a = (answer or "").strip()
    if not q or len(a) < 20:
        return None

    keyword = q[:80]
    for art in _articles.values():
        if art.get("keyword") == keyword and art.get("source") == "forum_qa":
            return {"skipped": True, "reason": "duplicate_forum_keyword", "article_id": art["id"]}

    art_id = f"forum_{_next_id}"
    _next_id += 1
    article = {
        "id": art_id,
        "keyword": keyword,
        "title": f"【论坛精选】{q[:100]}",
        "content": f"## 买家提问\n\n{q}\n\n## 采纳回答\n\n{a}\n\n---\n*来源：买家问答论坛，发布前请核对事实与合规表述。*",
        "style": "论坛精选",
        "status": "draft",
        "published_at": None,
        "views": 0,
        "source": "forum_qa",
        "human_review_required": True,
    }
    _articles[art_id] = article
    return article
