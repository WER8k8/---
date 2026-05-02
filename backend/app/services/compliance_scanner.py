"""合规检查服务 - 广告法检测引擎"""
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime


class ComplianceScanner:
    """合规扫描器 - 检测广告法违规内容"""
    
    def __init__(self, db):
        self.db = db
        self.keywords_cache = {}
        self._load_keywords()
    
    def _load_keywords(self):
        """加载违禁词缓存"""
        from app.models.compliance import AdvertisementLawKeyword
        
        keywords = self.db.query(AdvertisementLawKeyword).filter(AdvertisementLawKeyword.is_active == True).all()
        for kw in keywords:
            if kw.category not in self.keywords_cache:
                self.keywords_cache[kw.category] = []
            self.keywords_cache[kw.category].append({
                'keyword': kw.keyword,
                'severity': kw.severity,
                'description': kw.description,
                'alternative': kw.alternative
            })
    
    def scan_text(self, text: str) -> Dict[str, Any]:
        """扫描文本中的违规内容"""
        if not text:
            return {
                'success': True,
                'total_issues': 0,
                'high_severity_count': 0,
                'medium_severity_count': 0,
                'low_severity_count': 0,
                'violations': [],
                'suggestions': []
            }
        
        violations = []
        suggestions = []
        
        for category, keywords in self.keywords_cache.items():
            for kw in keywords:
                matches = self._find_matches(text, kw['keyword'])
                for match in matches:
                    violation = {
                        'keyword': kw['keyword'],
                        'category': category,
                        'severity': kw['severity'],
                        'matched_text': match['text'],
                        'context': match['context'],
                        'position': match['position'],
                        'description': kw['description'],
                        'alternative': kw['alternative']
                    }
                    violations.append(violation)
                    
                    if kw['alternative'] and kw['alternative'] not in suggestions:
                        suggestions.append(f"将 '{kw['keyword']}' 替换为 '{kw['alternative']}'")
        
        # 统计各严重程度的数量
        high_count = sum(1 for v in violations if v['severity'] == 'high')
        medium_count = sum(1 for v in violations if v['severity'] == 'medium')
        low_count = sum(1 for v in violations if v['severity'] == 'low')
        
        return {
            'success': True,
            'total_issues': len(violations),
            'high_severity_count': high_count,
            'medium_severity_count': medium_count,
            'low_severity_count': low_count,
            'violations': violations,
            'suggestions': suggestions
        }
    
    def _find_matches(self, text: str, keyword: str) -> List[Dict[str, Any]]:
        """查找文本中所有匹配的关键词"""
        matches = []
        pattern = re.escape(keyword)
        
        # 使用不区分大小写的匹配
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end]
            
            # 添加省略号指示
            if start > 0:
                context = '...' + context
            if end < len(text):
                context = context + '...'
            
            matches.append({
                'text': match.group(),
                'context': context,
                'position': {
                    'start': match.start(),
                    'end': match.end()
                }
            })
        
        return matches
    
    def scan_html(self, html_content: str) -> Dict[str, Any]:
        """扫描HTML内容中的违规内容"""
        import html
        
        # 移除HTML标签，只保留文本内容
        text = re.sub(r'<[^>]*>', ' ', html_content)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return self.scan_text(text)
    
    def validate_content(self, title: str, content: str) -> Dict[str, Any]:
        """验证内容合规性"""
        title_result = self.scan_text(title)
        content_result = self.scan_text(content)
        
        combined_violations = title_result['violations'] + content_result['violations']
        combined_suggestions = list(set(title_result['suggestions'] + content_result['suggestions']))
        
        return {
            'success': True,
            'title_issues': title_result['total_issues'],
            'content_issues': content_result['total_issues'],
            'total_issues': len(combined_violations),
            'high_severity_count': title_result['high_severity_count'] + content_result['high_severity_count'],
            'medium_severity_count': title_result['medium_severity_count'] + content_result['medium_severity_count'],
            'low_severity_count': title_result['low_severity_count'] + content_result['low_severity_count'],
            'violations': combined_violations,
            'suggestions': combined_suggestions,
            'is_compliant': len(combined_violations) == 0
        }
    
    def get_keyword_categories(self) -> List[str]:
        """获取所有违规词分类"""
        return list(self.keywords_cache.keys())
    
    def get_keywords_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类获取违规词"""
        return self.keywords_cache.get(category, [])
    
    def refresh_keywords(self):
        """刷新关键词缓存"""
        self._load_keywords()


# 初始化扫描器实例
compliance_scanner = None

def init_compliance_scanner(db):
    """初始化合规扫描器"""
    global compliance_scanner
    compliance_scanner = ComplianceScanner(db)
    return compliance_scanner


# 默认广告法违禁词数据（首次运行时初始化）
DEFAULT_AD_LAW_KEYWORDS = [
    # 极限词 - 最高级
    {'keyword': '最', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '较、非常'},
    {'keyword': '最佳', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '优质'},
    {'keyword': '顶级', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '高端'},
    {'keyword': '顶尖', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '优秀'},
    {'keyword': '顶级', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '高端'},
    {'keyword': '第一', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '领先'},
    {'keyword': '唯一', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用绝对化表述', 'alternative': '独特'},
    {'keyword': '首选', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '推荐'},
    {'keyword': '顶级品质', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '优质品质'},
    {'keyword': '最高级', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '高级'},
    {'keyword': '国家级', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用国家级等绝对化表述', 'alternative': '行业领先'},
    {'keyword': '世界级', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用世界级等绝对化表述', 'alternative': '国际水准'},
    {'keyword': '国家级', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用国家级等绝对化表述', 'alternative': '行业领先'},
    {'keyword': '全网第一', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '全网领先'},
    {'keyword': '销量第一', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '销量领先'},
    {'keyword': '排名第一', 'category': '极限词', 'severity': 'high', 'description': '广告法禁用最高级表述', 'alternative': '排名领先'},
    
    # 虚假宣传
    {'keyword': '100%', 'category': '虚假宣传', 'severity': 'high', 'description': '广告法禁用绝对化承诺', 'alternative': '接近100%'},
    {'keyword': '绝对', 'category': '虚假宣传', 'severity': 'high', 'description': '广告法禁用绝对化表述', 'alternative': '非常'},
    {'keyword': '保证', 'category': '虚假宣传', 'severity': 'medium', 'description': '广告法禁用保证类承诺', 'alternative': '承诺'},
    {'keyword': '包治', 'category': '虚假宣传', 'severity': 'high', 'description': '广告法禁用医疗类保证', 'alternative': '辅助改善'},
    {'keyword': '根治', 'category': '虚假宣传', 'severity': 'high', 'description': '广告法禁用医疗类保证', 'alternative': '有效缓解'},
    {'keyword': '无效退款', 'category': '虚假宣传', 'severity': 'medium', 'description': '广告法禁用承诺类表述', 'alternative': '不满意可退换'},
    {'keyword': '永不磨损', 'category': '虚假宣传', 'severity': 'high', 'description': '广告法禁用绝对化承诺', 'alternative': '耐磨耐用'},
    {'keyword': '永久', 'category': '虚假宣传', 'severity': 'high', 'description': '广告法禁用绝对化承诺', 'alternative': '长期'},
    
    # 医疗用语
    {'keyword': '治疗', 'category': '医疗用语', 'severity': 'high', 'description': '非医疗产品禁用医疗用语', 'alternative': '改善'},
    {'keyword': '治愈', 'category': '医疗用语', 'severity': 'high', 'description': '非医疗产品禁用医疗用语', 'alternative': '缓解'},
    {'keyword': '疗效', 'category': '医疗用语', 'severity': 'high', 'description': '非医疗产品禁用医疗用语', 'alternative': '效果'},
    {'keyword': '药', 'category': '医疗用语', 'severity': 'high', 'description': '非药品禁用药品相关表述', 'alternative': '产品'},
    {'keyword': '保健品', 'category': '医疗用语', 'severity': 'medium', 'description': '非保健品需谨慎使用', 'alternative': '健康产品'},
    {'keyword': '预防', 'category': '医疗用语', 'severity': 'high', 'description': '非医疗产品禁用预防类表述', 'alternative': '防护'},
    {'keyword': '杀菌', 'category': '医疗用语', 'severity': 'medium', 'description': '需有相关资质', 'alternative': '清洁'},
    {'keyword': '消毒', 'category': '医疗用语', 'severity': 'medium', 'description': '需有相关资质', 'alternative': '除菌'},
    
    # 权威性表述
    {'keyword': '专家推荐', 'category': '权威性表述', 'severity': 'medium', 'description': '广告法要求真实证明', 'alternative': '专业认可'},
    {'keyword': '权威认证', 'category': '权威性表述', 'severity': 'medium', 'description': '广告法要求真实证明', 'alternative': '行业认证'},
    {'keyword': '国家认证', 'category': '权威性表述', 'severity': 'high', 'description': '广告法要求真实证明', 'alternative': '国家标准'},
    {'keyword': '中科院', 'category': '权威性表述', 'severity': 'high', 'description': '广告法要求真实合作证明', 'alternative': '科研机构'},
    {'keyword': '专利', 'category': '权威性表述', 'severity': 'medium', 'description': '需提供专利号', 'alternative': '专有技术'},
    
    # 促销用语
    {'keyword': '限时', 'category': '促销用语', 'severity': 'low', 'description': '需明确时限', 'alternative': '限时特惠'},
    {'keyword': '特价', 'category': '促销用语', 'severity': 'low', 'description': '需真实价格对比', 'alternative': '优惠价'},
    {'keyword': '清仓', 'category': '促销用语', 'severity': 'low', 'description': '需真实库存情况', 'alternative': '特惠'},
    {'keyword': '亏本', 'category': '促销用语', 'severity': 'medium', 'description': '广告法要求真实', 'alternative': '让利'},
    {'keyword': '跳楼价', 'category': '促销用语', 'severity': 'medium', 'description': '广告法要求真实', 'alternative': '特惠价'},
    
    # 金融相关
    {'keyword': '保本', 'category': '金融用语', 'severity': 'high', 'description': '非金融机构禁用', 'alternative': '稳健'},
    {'keyword': '高收益', 'category': '金融用语', 'severity': 'high', 'description': '需有风险提示', 'alternative': '合理收益'},
    {'keyword': '无风险', 'category': '金融用语', 'severity': 'high', 'description': '广告法禁用', 'alternative': '低风险'},
]


def init_default_keywords(db):
    """初始化默认广告法违禁词"""
    from app.models.compliance import AdvertisementLawKeyword
    from uuid import uuid4
    
    # 检查是否已存在数据
    existing_count = db.query(AdvertisementLawKeyword).count()
    if existing_count > 0:
        return
    
    # 插入默认违禁词
    for kw_data in DEFAULT_AD_LAW_KEYWORDS:
        keyword = AdvertisementLawKeyword(
            id=str(uuid4()),
            keyword=kw_data['keyword'],
            category=kw_data['category'],
            severity=kw_data['severity'],
            description=kw_data['description'],
            alternative=kw_data['alternative']
        )
        db.add(keyword)
    
    db.commit()
