#!/usr/bin/env python3
"""SEO自动检查脚本 - GitHub Actions使用"""
import requests
import json
import sys
import re
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, Any, List

SITE_URL = "https://www.youdingjiancai.com"
RESULTS: Dict[str, Any] = {
    'timestamp': datetime.now().isoformat(),
    'site_url': SITE_URL,
    'checks': {},
    'issues': [],
    'warnings': [],
    'score': 100
}


def check_status_code():
    try:
        r = requests.get(SITE_URL, timeout=30)
        success = r.status_code == 200
        if not success:
            RESULTS['issues'].append(f"HTTP状态码异常: {r.status_code}")
            RESULTS['score'] -= 20
        return success, r.status_code
    except Exception as e:
        RESULTS['issues'].append(f"网站无法访问: {str(e)}")
        RESULTS['score'] -= 30
        return False, str(e)


def check_meta_tags():
    try:
        r = requests.get(SITE_URL, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        description = soup.find('meta', attrs={'name': 'description'})
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        
        title_length = len(title.string) if title and title.string else 0
        desc_length = len(description.get('content')) if description and description.get('content') else 0
        
        if title_length < 30 or title_length > 60:
            RESULTS['warnings'].append(f"标题长度不理想: {title_length}字符(建议30-60)")
            RESULTS['score'] -= 5
        
        if desc_length < 120 or desc_length > 160:
            RESULTS['warnings'].append(f"描述长度不理想: {desc_length}字符(建议120-160)")
            RESULTS['score'] -= 5
        
        if not og_title or not og_description or not og_image:
            RESULTS['warnings'].append("缺少Open Graph标签")
            RESULTS['score'] -= 10
        
        if not canonical:
            RESULTS['warnings'].append("缺少canonical标签")
            RESULTS['score'] -= 5
        
        return {
            'has_title': bool(title and title.string),
            'has_description': bool(description and description.get('content')),
            'has_keywords': bool(keywords and keywords.get('content')),
            'has_og_tags': bool(og_title and og_description and og_image),
            'has_canonical': bool(canonical),
            'title_length': title_length,
            'description_length': desc_length
        }
    except Exception as e:
        RESULTS['issues'].append(f"Meta标签检查失败: {str(e)}")
        RESULTS['score'] -= 15
        return {'error': str(e)}


def check_structured_data():
    try:
        r = requests.get(SITE_URL, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        
        structured_data_found = False
        for script in json_ld_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and '@context' in data:
                        structured_data_found = True
                        break
                except:
                    pass
        
        if not structured_data_found:
            RESULTS['warnings'].append("缺少结构化数据(Schema.org)")
            RESULTS['score'] -= 10
        
        return {'has_structured_data': structured_data_found, 'count': len(json_ld_scripts)}
    except Exception as e:
        return {'error': str(e)}


def check_robots_txt():
    try:
        r = requests.get(f"{SITE_URL}/robots.txt", timeout=10)
        if r.status_code != 200:
            RESULTS['warnings'].append("robots.txt不存在或无法访问")
            RESULTS['score'] -= 5
        return r.status_code == 200
    except:
        RESULTS['warnings'].append("robots.txt检查失败")
        return False


def check_sitemap():
    try:
        r = requests.get(f"{SITE_URL}/sitemap.xml", timeout=10)
        if r.status_code != 200:
            RESULTS['issues'].append("sitemap.xml不存在或无法访问")
            RESULTS['score'] -= 10
        else:
            soup = BeautifulSoup(r.text, 'xml')
            urls = soup.find_all('loc')
            return {'exists': True, 'url_count': len(urls)}
        return {'exists': False}
    except:
        RESULTS['warnings'].append("sitemap检查失败")
        return {'exists': False}


def check_llms_txt():
    try:
        r = requests.get(f"{SITE_URL}/llms.txt", timeout=10)
        if r.status_code != 200:
            RESULTS['warnings'].append("llms.txt不存在")
            RESULTS['score'] -= 5
        return r.status_code == 200
    except:
        return False


def check_performance():
    try:
        r = requests.get(SITE_URL, timeout=30)
        load_time = r.elapsed.total_seconds()
        
        if load_time > 5:
            RESULTS['issues'].append(f"加载时间过长: {load_time:.2f}秒")
            RESULTS['score'] -= 15
        elif load_time > 3:
            RESULTS['warnings'].append(f"加载时间偏长: {load_time:.2f}秒")
            RESULTS['score'] -= 5
        
        return load_time < 3, load_time
    except Exception as e:
        RESULTS['issues'].append(f"性能检查失败: {str(e)}")
        return False, str(e)


def check_https():
    if not SITE_URL.startswith('https://'):
        RESULTS['issues'].append("网站未使用HTTPS")
        RESULTS['score'] -= 20
        return False
    return True


def check_mobile_friendly():
    try:
        r = requests.get(SITE_URL, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        
        if not viewport:
            RESULTS['issues'].append("缺少viewport meta标签")
            RESULTS['score'] -= 15
            return False
        
        return True
    except Exception as e:
        RESULTS['warnings'].append(f"移动端友好检查失败: {str(e)}")
        return False


def check_links():
    try:
        r = requests.get(SITE_URL, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', href=True)
        
        broken_links = []
        internal_links = 0
        external_links = 0
        
        for link in links[:20]:
            href = link['href']
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            if href.startswith('/'):
                internal_links += 1
            else:
                external_links += 1
        
        return {
            'total_links': len(links),
            'internal_links': internal_links,
            'external_links': external_links
        }
    except Exception as e:
        return {'error': str(e)}


def check_images():
    try:
        r = requests.get(SITE_URL, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        images = soup.find_all('img')
        
        images_without_alt = 0
        for img in images:
            if not img.get('alt'):
                images_without_alt += 1
        
        if images_without_alt > 0:
            RESULTS['warnings'].append(f"{images_without_alt}张图片缺少alt属性")
            RESULTS['score'] -= 5
        
        return {
            'total_images': len(images),
            'images_with_alt': len(images) - images_without_alt,
            'images_without_alt': images_without_alt
        }
    except Exception as e:
        return {'error': str(e)}


def generate_report():
    RESULTS['score'] = max(0, RESULTS['score'])
    
    if RESULTS['score'] >= 90:
        RESULTS['grade'] = 'A'
    elif RESULTS['score'] >= 80:
        RESULTS['grade'] = 'B'
    elif RESULTS['score'] >= 70:
        RESULTS['grade'] = 'C'
    elif RESULTS['score'] >= 60:
        RESULTS['grade'] = 'D'
    else:
        RESULTS['grade'] = 'F'
    
    if RESULTS['issues']:
        RESULTS['overall_status'] = 'FAILED'
    else:
        RESULTS['overall_status'] = 'PASSED'
    
    report_filename = f'seo-report-{datetime.now().strftime("%Y%m%d")}.json'
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"SEO检查报告")
    print(f"{'='*50}")
    print(f"网站: {SITE_URL}")
    print(f"时间: {RESULTS['timestamp']}")
    print(f"得分: {RESULTS['score']}/100 (等级: {RESULTS['grade']})")
    print(f"状态: {RESULTS['overall_status']}")
    
    if RESULTS['issues']:
        print(f"\n问题 ({len(RESULTS['issues'])}):")
        for issue in RESULTS['issues']:
            print(f"  ❌ {issue}")
    
    if RESULTS['warnings']:
        print(f"\n警告 ({len(RESULTS['warnings'])}):")
        for warning in RESULTS['warnings']:
            print(f"  ⚠️ {warning}")
    
    print(f"\n详细报告: {report_filename}")
    print(f"{'='*50}\n")


def main():
    print("开始SEO检查...")
    
    RESULTS['checks']['https'] = check_https()
    RESULTS['checks']['status_code'] = check_status_code()
    RESULTS['checks']['meta_tags'] = check_meta_tags()
    RESULTS['checks']['structured_data'] = check_structured_data()
    RESULTS['checks']['robots_txt'] = check_robots_txt()
    RESULTS['checks']['sitemap'] = check_sitemap()
    RESULTS['checks']['llms_txt'] = check_llms_txt()
    RESULTS['checks']['performance'] = check_performance()
    RESULTS['checks']['mobile_friendly'] = check_mobile_friendly()
    RESULTS['checks']['links'] = check_links()
    RESULTS['checks']['images'] = check_images()
    
    generate_report()
    
    if RESULTS['overall_status'] == 'FAILED':
        sys.exit(1)


if __name__ == '__main__':
    main()
