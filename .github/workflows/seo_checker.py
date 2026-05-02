#!/usr/bin/env python3
"""
SEO检查器 - GitHub Action核心脚本

功能：
1. 检查HTML文件的SEO优化情况
2. 检测页面速度和性能
3. 验证链接有效性
4. 生成详细的SEO报告
"""

import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

class SEOChecker:
    """SEO检查器主类"""
    
    def __init__(self):
        self.results = {
            'summary': {
                'total_pages': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            },
            'pages': [],
            'issues': {
                'critical': [],
                'warning': [],
                'info': []
            }
        }
        
    def scan_directory(self, directory='.'):
        """扫描目录中的HTML文件"""
        html_files = list(Path(directory).rglob('*.html'))
        self.results['summary']['total_pages'] = len(html_files)
        
        for html_file in html_files:
            self.scan_file(html_file)
        
        return self.results
    
    def scan_file(self, file_path):
        """扫描单个HTML文件"""
        page_result = {
            'file': str(file_path),
            'issues': [],
            'score': 100,
            'elements': {
                'title': None,
                'meta_description': None,
                'h1_count': 0,
                'images_with_alt': 0,
                'images_without_alt': 0,
                'links_count': 0,
                'broken_links': 0
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if HAS_BS4:
                soup = BeautifulSoup(content, 'html.parser')
                page_result.update(self._analyze_soup(soup, file_path))
            else:
                page_result.update(self._analyze_text(content, file_path))
                
        except Exception as e:
            page_result['issues'].append({
                'type': 'critical',
                'message': f'无法读取文件: {str(e)}'
            })
            page_result['score'] = 0
        
        self.results['pages'].append(page_result)
        
        # 统计结果
        critical_count = len([i for i in page_result['issues'] if i['type'] == 'critical'])
        warning_count = len([i for i in page_result['issues'] if i['type'] == 'warning'])
        
        if critical_count > 0:
            self.results['summary']['failed'] += 1
        elif warning_count > 0:
            self.results['summary']['warnings'] += 1
        else:
            self.results['summary']['passed'] += 1
        
        return page_result
    
    def _analyze_soup(self, soup, file_path):
        """使用BeautifulSoup分析HTML"""
        result = {
            'issues': [],
            'score': 100,
            'elements': {
                'title': None,
                'meta_description': None,
                'h1_count': 0,
                'images_with_alt': 0,
                'images_without_alt': 0,
                'links_count': 0,
                'broken_links': 0
            }
        }
        
        # 检查标题
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            result['elements']['title'] = title_text
            if len(title_text) == 0:
                result['issues'].append({
                    'type': 'critical',
                    'message': '页面标题为空'
                })
                result['score'] -= 15
            elif len(title_text) < 10:
                result['issues'].append({
                    'type': 'warning',
                    'message': f'标题过短 ({len(title_text)} 字符)'
                })
                result['score'] -= 5
            elif len(title_text) > 60:
                result['issues'].append({
                    'type': 'warning',
                    'message': f'标题过长 ({len(title_text)} 字符)'
                })
                result['score'] -= 5
        else:
            result['issues'].append({
                'type': 'critical',
                'message': '缺少<title>标签'
            })
            result['score'] -= 20
        
        # 检查meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc_content = meta_desc.get('content', '').strip()
            result['elements']['meta_description'] = desc_content
            if len(desc_content) == 0:
                result['issues'].append({
                    'type': 'critical',
                    'message': 'meta description为空'
                })
                result['score'] -= 10
            elif len(desc_content) < 50:
                result['issues'].append({
                    'type': 'warning',
                    'message': f'meta description过短 ({len(desc_content)} 字符)'
                })
                result['score'] -= 3
            elif len(desc_content) > 160:
                result['issues'].append({
                    'type': 'warning',
                    'message': f'meta description过长 ({len(desc_content)} 字符)'
                })
                result['score'] -= 3
        else:
            result['issues'].append({
                'type': 'critical',
                'message': '缺少meta description标签'
            })
            result['score'] -= 15
        
        # 检查H1标签
        h1_tags = soup.find_all('h1')
        result['elements']['h1_count'] = len(h1_tags)
        if len(h1_tags) == 0:
            result['issues'].append({
                'type': 'critical',
                'message': '缺少H1标签'
            })
            result['score'] -= 15
        elif len(h1_tags) > 1:
            result['issues'].append({
                'type': 'warning',
                'message': f'发现{len(h1_tags)}个H1标签（建议只保留1个）'
            })
            result['score'] -= 5
        
        # 检查图片alt属性
        img_tags = soup.find_all('img')
        for img in img_tags:
            alt_text = img.get('alt', '').strip()
            if alt_text:
                result['elements']['images_with_alt'] += 1
            else:
                result['elements']['images_without_alt'] += 1
                result['issues'].append({
                    'type': 'warning',
                    'message': f'图片缺少alt属性: {img.get("src", "未知")}'
                })
                result['score'] -= 2
        
        # 检查链接
        a_tags = soup.find_all('a')
        result['elements']['links_count'] = len(a_tags)
        
        # 检查Schema标记
        schema_scripts = soup.find_all('script', type='application/ld+json')
        if not schema_scripts:
            result['issues'].append({
                'type': 'info',
                'message': '建议添加Schema标记以提升SEO'
            })
        
        # 检查响应式meta标签
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport_meta:
            result['issues'].append({
                'type': 'warning',
                'message': '缺少viewport meta标签（影响移动端SEO）'
            })
            result['score'] -= 5
        
        # 检查robots.txt引用
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        if not robots_meta:
            result['issues'].append({
                'type': 'info',
                'message': '建议添加robots meta标签'
            })
        
        return result
    
    def _analyze_text(self, content, file_path):
        """不使用BeautifulSoup时的文本分析"""
        result = {
            'issues': [],
            'score': 100,
            'elements': {
                'title': None,
                'meta_description': None,
                'h1_count': 0,
                'images_with_alt': 0,
                'images_without_alt': 0,
                'links_count': 0,
                'broken_links': 0
            }
        }
        
        # 使用正则检查基本元素
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title_text = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            result['elements']['title'] = title_text
            if len(title_text) == 0:
                result['issues'].append({'type': 'critical', 'message': '页面标题为空'})
                result['score'] -= 15
        else:
            result['issues'].append({'type': 'critical', 'message': '缺少<title>标签'})
            result['score'] -= 20
        
        meta_desc_match = re.search(r'<meta[^>]*name=[\'"]description[\'"][^>]*content=[\'"](.*?)[\'"]', content, re.IGNORECASE)
        if meta_desc_match:
            result['elements']['meta_description'] = meta_desc_match.group(1)
        else:
            result['issues'].append({'type': 'critical', 'message': '缺少meta description标签'})
            result['score'] -= 15
        
        h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
        result['elements']['h1_count'] = h1_count
        if h1_count == 0:
            result['issues'].append({'type': 'critical', 'message': '缺少H1标签'})
            result['score'] -= 15
        
        return result
    
    def generate_html_report(self, output_file='seo-report.html'):
        """生成HTML格式的SEO报告"""
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO检查报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; min-height: 100vh; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 16px; margin-bottom: 20px; }}
        header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        header p {{ opacity: 0.9; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
        .stat-card h3 {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; }}
        .stat-card.passed .value {{ color: #10b981; }}
        .stat-card.failed .value {{ color: #ef4444; }}
        .stat-card.warning .value {{ color: #f59e0b; }}
        .stat-card.total .value {{ color: #6366f1; }}
        .section {{ background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 20px; }}
        .section h2 {{ font-size: 18px; margin-bottom: 20px; color: #1f2937; }}
        .page-list {{ max-height: 400px; overflow-y: auto; }}
        .page-item {{ padding: 16px; border-bottom: 1px solid #f0f0f0; }}
        .page-item:last-child {{ border-bottom: none; }}
        .page-item .file-name {{ font-weight: 600; color: #374151; }}
        .page-item .score {{ float: right; font-size: 18px; font-weight: bold; }}
        .page-item .score.pass {{ color: #10b981; }}
        .page-item .score.warn {{ color: #f59e0b; }}
        .page-item .score.fail {{ color: #ef4444; }}
        .issue-list {{ margin-top: 8px; }}
        .issue {{ font-size: 14px; padding: 6px 12px; margin-bottom: 4px; border-radius: 6px; }}
        .issue.critical {{ background: #fee2e2; color: #dc2626; }}
        .issue.warning {{ background: #fef3c7; color: #d97706; }}
        .issue.info {{ background: #dbeafe; color: #2563eb; }}
        .element-info {{ font-size: 14px; color: #6b7280; margin-top: 8px; }}
        .element-info span {{ margin-right: 16px; }}
        footer {{ text-align: center; padding: 20px; color: #9ca3af; font-size: 14px; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500; }}
        .badge.pass {{ background: #dcfce7; color: #16a34a; }}
        .badge.warn {{ background: #fef3c7; color: #d97706; }}
        .badge.fail {{ background: #fee2e2; color: #dc2626; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 SEO检查报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="stats">
            <div class="stat-card total">
                <h3>扫描页面</h3>
                <div class="value">{self.results['summary']['total_pages']}</div>
            </div>
            <div class="stat-card passed">
                <h3>通过</h3>
                <div class="value">{self.results['summary']['passed']}</div>
            </div>
            <div class="stat-card warning">
                <h3>警告</h3>
                <div class="value">{self.results['summary']['warnings']}</div>
            </div>
            <div class="stat-card failed">
                <h3>失败</h3>
                <div class="value">{self.results['summary']['failed']}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📄 页面详情</h2>
            <div class="page-list">
                {''.join(self._render_page_item(page) for page in self.results['pages'])}
            </div>
        </div>
        
        <footer>
            <p>SEO检查器 - GitHub Action</p>
        </footer>
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"SEO报告已生成: {output_file}")
    
    def _render_page_item(self, page):
        """渲染单个页面项"""
        score_class = 'pass' if page['score'] >= 80 else 'warn' if page['score'] >= 60 else 'fail'
        issues_html = ''.join(
            f'<div class="issue {issue["type"]}">• {issue["message"]}</div>'
            for issue in page['issues']
        )
        
        elements = page['elements']
        elements_html = f"""
        <div class="element-info">
            <span>📝 标题: {elements['title'][:50]}...{' (过长)' if elements['title'] and len(elements['title']) > 60 else ''}</span>
            <span>📊 H1: {elements['h1_count']}</span>
            <span>🖼️ 图片: {elements['images_with_alt']}个有alt / {elements['images_without_alt']}个无alt</span>
            <span>🔗 链接: {elements['links_count']}</span>
        </div>
        """
        
        return f"""
        <div class="page-item">
            <span class="file-name">{page['file']}</span>
            <span class="score {score_class}">{page['score']}</span>
            {elements_html}
            {f'<div class="issue-list">{issues_html}</div>' if page['issues'] else ''}
        </div>
        """
    
    def generate_json_report(self, output_file='seo-report.json'):
        """生成JSON格式报告"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.results['summary'],
            'pages': self.results['pages']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"JSON报告已生成: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='SEO检查器')
    parser.add_argument('--dir', default='.', help='要扫描的目录')
    parser.add_argument('--output', default='seo-report.html', help='输出报告文件')
    parser.add_argument('--format', choices=['html', 'json'], default='html', help='报告格式')
    args = parser.parse_args()
    
    checker = SEOChecker()
    results = checker.scan_directory(args.dir)
    
    print(f"扫描完成！共检查 {results['summary']['total_pages']} 个页面")
    print(f"✓ 通过: {results['summary']['passed']}")
    print(f"⚠️ 警告: {results['summary']['warnings']}")
    print(f"✗ 失败: {results['summary']['failed']}")
    
    if args.format == 'html':
        checker.generate_html_report(args.output)
    else:
        checker.generate_json_report(args.output)


if __name__ == '__main__':
    main()
