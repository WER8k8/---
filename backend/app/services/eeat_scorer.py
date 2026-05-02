import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

class EEATScorer:
    """EEAT评分器 - 评估内容的Experience, Expertise, Authoritativeness, Trustworthiness"""
    
    def __init__(self):
        self.positive_trust_signals = [
            'has_about_page',
            'has_contact_page',
            'has_privacy_policy',
            'has_terms_of_service',
            'has_author_bio',
            'has_author_credentials',
            'has_external_references',
            'has_citations',
            'has_updated_date',
            'has_ssl_certificate',
            'has_secure_connection',
            'has_social_proof',
            'has_media_mentions',
            'has_industry_awards',
            'has_expert_reviews',
        ]
        
        self.negative_trust_signals = [
            'missing_about_page',
            'missing_contact_info',
            'no_author_credibility',
            'outdated_content',
            'spammy_keyword_stuffing',
            'excessive_ads',
            'malicious_content',
            'plagiarized_content',
            'broken_links',
            'poor_grammar',
            'inconsistent_branding',
        ]
    
    def calculate_experience_score(self, content_data: Dict[str, Any]) -> float:
        """计算经验评分 (0-100)"""
        score = 0
        factors = []
        
        # 作者经验年限
        if 'author_experience_years' in content_data:
            years = content_data['author_experience_years']
            score += min(years * 2, 20)
            factors.append(f"作者经验年限: {years}年")
        
        # 内容深度
        if 'content_depth' in content_data:
            depth = content_data['content_depth']  # basic, intermediate, advanced, expert
            depth_scores = {'basic': 5, 'intermediate': 15, 'advanced': 25, 'expert': 35}
            score += depth_scores.get(depth, 5)
            factors.append(f"内容深度: {depth}")
        
        # 实践案例数量
        if 'case_studies_count' in content_data:
            cases = content_data['case_studies_count']
            score += min(cases * 3, 15)
            factors.append(f"实践案例: {cases}个")
        
        # 项目经验
        if 'project_experience' in content_data:
            projects = content_data['project_experience']
            score += min(len(projects) * 2, 10)
            factors.append(f"项目经验: {len(projects)}个")
        
        # 行业从业背景
        if 'industry_background' in content_data and content_data['industry_background']:
            score += 20
            factors.append("具备行业从业背景")
        
        return min(score, 100), factors
    
    def calculate_expertise_score(self, content_data: Dict[str, Any]) -> float:
        """计算专业知识评分 (0-100)"""
        score = 0
        factors = []
        
        # 专业认证
        if 'certifications' in content_data:
            certs = content_data['certifications']
            score += min(len(certs) * 10, 30)
            factors.append(f"专业认证: {len(certs)}项")
        
        # 教育背景
        if 'education_level' in content_data:
            level = content_data['education_level']  # high_school, bachelor, master, phd
            level_scores = {'high_school': 5, 'bachelor': 15, 'master': 25, 'phd': 35}
            score += level_scores.get(level, 5)
            factors.append(f"教育背景: {level}")
        
        # 专业领域匹配度
        if 'topic_match_score' in content_data:
            match_score = content_data['topic_match_score']
            score += match_score * 0.3
            factors.append(f"专业匹配度: {match_score}%")
        
        # 发表论文/研究
        if 'publications' in content_data:
            pubs = content_data['publications']
            score += min(len(pubs) * 5, 15)
            factors.append(f"发表论文: {len(pubs)}篇")
        
        # 专业会员资格
        if 'professional_memberships' in content_data:
            memberships = content_data['professional_memberships']
            score += min(len(memberships) * 5, 15)
            factors.append(f"专业会员: {len(memberships)}个")
        
        return min(score, 100), factors
    
    def calculate_authoritativeness_score(self, content_data: Dict[str, Any]) -> float:
        """计算权威性评分 (0-100)"""
        score = 0
        factors = []
        
        # 媒体引用
        if 'media_mentions' in content_data:
            mentions = content_data['media_mentions']
            score += min(len(mentions) * 8, 32)
            factors.append(f"媒体引用: {len(mentions)}次")
        
        # 行业奖项
        if 'industry_awards' in content_data:
            awards = content_data['industry_awards']
            score += min(len(awards) * 10, 25)
            factors.append(f"行业奖项: {len(awards)}项")
        
        # 演讲/培训经历
        if 'speaking_engagements' in content_data:
            engagements = content_data['speaking_engagements']
            score += min(len(engagements) * 3, 15)
            factors.append(f"演讲经历: {len(engagements)}次")
        
        # 同行认可度
        if 'peer_recognition' in content_data:
            recognition = content_data['peer_recognition']
            score += recognition * 0.2
            factors.append(f"同行认可度: {recognition}%")
        
        # 行业影响力
        if 'industry_influence' in content_data:
            influence = content_data['industry_influence']  # low, medium, high, very_high
            influence_scores = {'low': 5, 'medium': 15, 'high': 25, 'very_high': 30}
            score += influence_scores.get(influence, 5)
            factors.append(f"行业影响力: {influence}")
        
        return min(score, 100), factors
    
    def calculate_trustworthiness_score(self, content_data: Dict[str, Any]) -> float:
        """计算可信度评分 (0-100)"""
        score = 50  # 基础分数
        factors = []
        
        # 信任信号
        if 'trust_signals' in content_data:
            signals = content_data['trust_signals']
            
            for signal in signals:
                if signal in self.positive_trust_signals:
                    score += 3
                    factors.append(f"正面信号: {signal}")
                elif signal in self.negative_trust_signals:
                    score -= 5
                    factors.append(f"负面信号: {signal}")
        
        # 内容准确性
        if 'fact_check_score' in content_data:
            fact_score = content_data['fact_check_score']
            score += (fact_score - 50) * 0.3
            factors.append(f"事实核查评分: {fact_score}%")
        
        # 透明性
        if 'transparency_score' in content_data:
            transparency = content_data['transparency_score']
            score += (transparency - 50) * 0.2
            factors.append(f"透明度评分: {transparency}%")
        
        # 隐私政策和使用条款
        if 'has_privacy_policy' in content_data and content_data['has_privacy_policy']:
            score += 5
            factors.append("有隐私政策")
        if 'has_terms_of_service' in content_data and content_data['has_terms_of_service']:
            score += 5
            factors.append("有服务条款")
        
        return max(0, min(score, 100)), factors
    
    def evaluate_eeat(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """综合评估EEAT分数"""
        experience_score, exp_factors = self.calculate_experience_score(content_data)
        expertise_score, exp_factors = self.calculate_expertise_score(content_data)
        authoritativeness_score, auth_factors = self.calculate_authoritativeness_score(content_data)
        trustworthiness_score, trust_factors = self.calculate_trustworthiness_score(content_data)
        
        # 计算综合分数 (加权平均)
        overall_score = (
            experience_score * 0.20 +
            expertise_score * 0.25 +
            authoritativeness_score * 0.25 +
            trustworthiness_score * 0.30
        )
        
        # 生成改进建议
        recommendations = self.generate_recommendations(
            experience_score,
            expertise_score,
            authoritativeness_score,
            trustworthiness_score
        )
        
        return {
            'experience_score': round(experience_score, 2),
            'expertise_score': round(expertise_score, 2),
            'authoritativeness_score': round(authoritativeness_score, 2),
            'trustworthiness_score': round(trustworthiness_score, 2),
            'overall_score': round(overall_score, 2),
            'factors': {
                'experience': exp_factors,
                'expertise': exp_factors,
                'authoritativeness': auth_factors,
                'trustworthiness': trust_factors,
            },
            'recommendations': recommendations,
            'evaluated_at': datetime.utcnow().isoformat(),
        }
    
    def generate_recommendations(self, exp: float, exp_score: float, auth: float, trust: float) -> List[str]:
        """根据评分生成改进建议"""
        recommendations = []
        
        thresholds = {
            'excellent': 80,
            'good': 60,
            'fair': 40,
            'poor': 0,
        }
        
        if exp < thresholds['good']:
            recommendations.append("建议增加作者的从业经验介绍，包括项目案例和工作经历")
        
        if exp_score < thresholds['good']:
            recommendations.append("建议补充作者的专业资质证明，如学历、认证证书等")
        
        if auth < thresholds['good']:
            recommendations.append("建议增加媒体报道、行业奖项等权威性证明")
        
        if trust < thresholds['good']:
            recommendations.append("建议完善网站的信任信号，包括隐私政策、联系方式等")
        
        if exp < thresholds['fair']:
            recommendations.append("紧急：需要显著提升作者的经验展示")
        
        if trust < thresholds['fair']:
            recommendations.append("紧急：网站可信度存在风险，需要立即修复")
        
        # 积极建议
        if exp >= thresholds['excellent']:
            recommendations.append("经验展示优秀，继续保持")
        
        if exp_score >= thresholds['excellent']:
            recommendations.append("专业资质完善，继续保持")
        
        return recommendations
    
    def get_trust_signal_categories(self) -> Dict[str, List[str]]:
        """获取信任信号分类"""
        return {
            'positive': self.positive_trust_signals,
            'negative': self.negative_trust_signals,
        }
