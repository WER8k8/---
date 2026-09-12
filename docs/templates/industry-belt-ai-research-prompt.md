# 大城 + 河间 · 建筑相关产品名调研 Prompt 模板

> PM 派工：`pm-langfang-industry-belt-ai-research-charter.md`  
> 执行：`scripts/run-industry-belt-ai-research.py`（默认 `--region dacheng_hejian`）

---

## 核心调研问题（PM 派给各 AI 大模型的同一句话）

```text
河北省廊坊市大城县和沧州市河间市这一带，当地工厂常出货的、
跟建筑/工地/工程相关的「产品名字」有哪些？
请尽量列全：主材 + 附属配套（如网格布、阴阳角、保温钉、防火/防腐涂料、
密封件、砂浆、板材、管道保温等），按品类分组。
不确定的品名标注「待核实」，不要编造。
```

---

## 系统角色（每条请求前置）

```text
你是 B2B 建材产业带调研助手，只做事实型品名清单整理，不编造不存在的工厂或虚假国标。
若不确定，请在 notes 写「待核实」，不要捏造 evidence 或 URL。
输出必须是合法 JSON，不要 markdown 代码块包裹。
```

---

## 用户 Prompt · 区域全量模式（默认 `{region_label}` = 大城县 + 河间市）

```text
{系统角色}

调研区域：{region_label}
重点乡镇/园区（可参考、可补充）：{towns}

请回答：这一带跟 **建筑、工地、工程** 相关的 **产品名字** 有哪些？

必须覆盖（但不限于）：
1. **主材**：岩棉、玻璃棉、橡塑、聚氨酯、XPS、酚醛、硅酸铝、夹芯板、净化板、冷库板等
2. **防火类**：钢结构防火涂料（薄/厚/超薄型）、饰面型防火涂料、防火封堵（阻火包/堵料/模块）等
3. **防腐类**：环氧/聚氨酯/氟碳等防腐涂料
4. **附属配套**：网格布、耐碱网格布、阴阳角、护角条、分隔条、保温钉、锚固件、电焊网、
   粘结/抹面/抗裂砂浆、打包带、胶带等
5. **河间配套**：橡塑密封条、垫片、软接头、管道密封等（若属河间集群）

每个品名一条记录，字段：
- name：中文品名（行业常用叫法）
- aliases：别名（数组，可空）
- specs_common：常见规格说法（数组，可空）
- town_cluster：相对集中在大城还是河间、哪个镇/园区（不确定写「待核实」）
- product_role：main（主材）| accessory（附属配套）| coating（涂料/油漆类）| sealing（密封/封堵类）
- export_suitable：是否常见外贸（true/false）
- notes：备注
- evidence：依据类型（Gov稿/B2B目录/行业常识），勿伪造链接

按品类分组输出 categories（至少 8 个分组），每组 ≥5 个品名；全区域合计尽量 ≥80 个不重复品名。
另给 recommended_seo_keywords：20～40 个采购商可能搜的中文长尾词。

严格输出 JSON：
{
  "region": "{region_label}",
  "research_question": "大城和河间一带有哪些建筑相关产品及附属配套品名",
  "categories": [
    {
      "category_id": "main_insulation",
      "category_name_zh": "保温绝热主材",
      "products": [ ... ]
    }
  ],
  "recommended_seo_keywords": [ ... ],
  "research_limits": "哪些品类或品名你不确定"
}
```

### 建议 category_id 对照（模型可增不可乱编大类）

| category_id | 中文分组 |
|-------------|----------|
| `main_insulation` | 保温绝热主材 |
| `steel_fire_coating` | 钢结构/电缆防火涂料 |
| `fire_coating_general` | 其他防火涂料 |
| `anti_corrosion_coating` | 防腐涂料 |
| `fire_sealing` | 防火封堵 |
| `panel_system` | 夹芯板/净化板/冷库板 |
| `finish_accessories` | 网格布/阴阳角/护角/分隔条 |
| `fixing_accessories` | 保温钉/锚固/电焊网 |
| `mortar_adhesive` | 砂浆/胶粘 |
| `pipe_support` | 管道支架/管壳/保温管 |
| `packaging` | 打包辅材 |
| `hejian_rubber` | 河间橡塑密封配套 |
| `misc_building` | 其他建筑相关（慎用，须 notes 说明） |

---

## 用户 Prompt · 单品类加深模式（可选 `--category`）

单品类时仍用区域语境，但只深挖一类：

```text
在 {region_label} 产业带，请只列「{category_name_zh}」下的工厂常出货品名（≥15 个）……
（字段同上，输出单组 categories 即可）
```

---

## PM 共识规则（脚本已实现）

1. 同一 `name`（归一化后）被 **≥2 个模型** 提到 → 高共识  
2. 仅 1 个模型 → notes 加「单模型提及，待复核」  
3. 区域模式按 `category_id + name` 去重合并  
4. 模型返回非 JSON → 仅存 `ai_raw/`，不参与共识

---

## 人工复核 checklist（GW-MR）

- [ ] 随机 10 品名在 Made-in-China / 1688 / 县域官网能搜到  
- [ ] 删去明显幻觉品名  
- [ ] 确认 **附属配套** 未漏大类（网格布、护角、钉子、密封等）  
- [ ] 补 `evidence_refs` 后交 PM-07
