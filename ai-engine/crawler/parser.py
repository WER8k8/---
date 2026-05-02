import json
import re
from typing import Optional
from bs4 import BeautifulSoup


class PageParser:
    TECHNICAL_PARAM_PATTERNS = {
        "density": r"(\d+(?:\.\d+)?)\s*(?:kg/m[³3]|千克/立方米)",
        "strength_grade": r"LC\d+(?:\.\d+)?",
        "thermal_conductivity": r"(\d+(?:\.\d+)?)\s*W/(?:m[·•]?K|米[·•]?开)",
        "particle_size": r"(\d+(?:\.\d+)?(?:～|~|-)\d+(?:\.\d+)?)\s*mm",
        "water_absorption": r"(\d+(?:\.\d+)?)\s*%",
    }

    def parse_html(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return {
            "title": soup.title.string.strip() if soup.title else "",
            "headings": self._extract_headings(soup),
            "paragraphs": self._extract_paragraphs(soup),
            "images": self._extract_images(soup),
            "links": self._extract_links(soup),
            "structured_data": self._extract_structured_data(soup),
            "clean_text": soup.get_text(separator="\n", strip=True),
        }

    def _extract_headings(self, soup: BeautifulSoup) -> dict:
        headings = {}
        for level in range(1, 7):
            tags = soup.find_all(f"h{level}")
            if tags:
                headings[f"h{level}"] = [h.get_text(strip=True) for h in tags]
        return headings

    def _extract_paragraphs(self, soup: BeautifulSoup) -> list[str]:
        return [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 10]

    def _extract_images(self, soup: BeautifulSoup) -> list[dict]:
        images = []
        for img in soup.find_all("img", src=True):
            alt = img.get("alt", "").strip()
            images.append({
                "src": img["src"],
                "alt": alt,
                "has_alt": bool(alt),
                "width": img.get("width"),
                "height": img.get("height"),
            })
        return images

    def _extract_links(self, soup: BeautifulSoup) -> list[dict]:
        links = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            links.append({
                "href": a["href"],
                "text": text,
                "has_text": bool(text),
                "nofollow": "nofollow" in a.get("rel", []),
            })
        return links

    def _extract_structured_data(self, soup: BeautifulSoup) -> list[dict]:
        scripts = soup.find_all("script", type="application/ld+json")
        results = []
        for script in scripts:
            try:
                data = json.loads(script.string)
                results.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        return results

    def extract_technical_params(self, text: str) -> dict:
        params = {}
        for name, pattern in self.TECHNICAL_PARAM_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                params[name] = matches
        return params

    def extract_keyword_density(self, text: str, keyword: str) -> float:
        if not text or not keyword:
            return 0.0
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        count = text_lower.count(keyword_lower)
        total_words = len(text_lower.split())
        return round((count / max(total_words, 1)) * 100, 2)

    def extract_eeat_signals(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        signals = {
            "author_info": bool(soup.find(class_=re.compile(r"author|byline|writer"))),
            "references": bool(soup.find(class_=re.compile(r"reference|citation|source"))),
            "date_published": bool(soup.find(class_=re.compile(r"date|time|published"))),
            "certifications": bool(soup.find(class_=re.compile(r"certif|license|qualif"))),
        }
        signals["score"] = sum(1 for v in signals.values() if v)
        return signals
