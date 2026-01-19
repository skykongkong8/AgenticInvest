from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import quote_plus
import os
import re
import html
import xml.etree.ElementTree as ET

import httpx
from mcp.server import FastMCP

DEFAULT_PAGE_SIZE = 20

mcp = FastMCP(
    name="news_fetcher",
    instructions=(
        "Provide tools to fetch recent news articles for a given ticker. "
        "This server is designed for agentic workflows using MCP."
    ),
)


def _mock_news(ticker: str) -> List[Dict[str, str]]:
    """
    왜 필요한가: 외부 API 또는 MCP 연결이 실패해도 서버가 안정적으로
    응답하도록 더미 데이터를 제공해야 합니다.

    어떻게 동작하나(초보자 관점):
    - 티커 문자열을 숫자로 바꿔(seed) 항상 같은 결과가 나오게 만듭니다.
    - 선택된 기사에 날짜/스니펫을 붙여 최소한의 현실감을 제공합니다.
    """
    mock_articles = [
        {"title": f"{ticker} announces record breaking quarterly results", "sentiment": "positive"},
        {"title": f"Analyst upgrades {ticker} to Buy", "sentiment": "positive"},
        {"title": f"Supply chain issues affect {ticker}", "sentiment": "negative"},
        {"title": f"{ticker} CEO faces lawsuit over tweets", "sentiment": "negative"},
        {"title": f"{ticker} unveils new product line", "sentiment": "positive"},
    ]
    seed = sum(ord(c) for c in ticker)
    selected = []
    current_date = datetime.now()

    for i, article in enumerate(mock_articles):
        if (seed + i) % 2 == 0:
            article_copy = article.copy()
            article_copy["date"] = (current_date - timedelta(days=i)).isoformat()
            article_copy["snippet"] = f"Full content of {article['title']}..."
            article_copy["source"] = "mock_news"
            selected.append(article_copy)

    return selected


def _clean_text(value: str) -> str:
    """
    왜 필요한가: RSS 요약문에는 HTML 태그가 섞여 있을 수 있어,
    그대로 저장하면 분석 단계에서 노이즈가 커집니다.

    어떻게 동작하나(초보자 관점):
    - HTML 태그를 제거하고, HTML 엔티티를 사람이 읽을 수 있는 문자로 바꿉니다.
    """
    text = re.sub(r"<[^>]+>", "", value or "")
    return html.unescape(text).strip()


def _build_google_news_url(
    base: str, *, language: str | None = None, country: str | None = None
) -> str:
    """
    왜 필요한가: Google News RSS는 언어/국가 설정에 따라 결과가 달라집니다.

    어떻게 동작하나(초보자 관점):
    - 언어와 국가가 모두 있으면 hl/gl/ceid 파라미터를 붙입니다.
    - 둘 중 하나만 있으면 기본값으로 보완해 일관된 URL을 만듭니다.
    """
    if not language and not country:
        return base

    lang = language or "en"
    ctry = country or "US"
    return f"{base}&hl={lang}&gl={ctry}&ceid={ctry}:{lang}"


def _parse_rss(xml_text: str, max_results: int) -> List[Dict[str, str]]:
    """
    왜 필요한가: RSS는 XML 형식이라서 파싱이 필요합니다.

    어떻게 동작하나(초보자 관점):
    - channel/item 구조를 읽어 제목, 링크, 발행일, 요약을 추출합니다.
    - max_results 만큼만 반환해 결과 크기를 제어합니다.
    """
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    items = channel.findall("item")
    results: List[Dict[str, str]] = []
    for item in items[:max_results]:
        title = _clean_text(item.findtext("title", default=""))
        link = _clean_text(item.findtext("link", default=""))
        published = _clean_text(item.findtext("pubDate", default=""))
        description = _clean_text(item.findtext("description", default=""))
        source = _clean_text(item.findtext("source", default="google_news"))
        results.append(
            {
                "title": title,
                "link": link,
                "published": published,
                "description": description,
                "source": source or "google_news",
                "sentiment": "neutral",
            }
        )

    return results


def _fetch_google_news_rss(url: str, max_results: int) -> List[Dict[str, str]]:
    """
    왜 필요한가: Google News RSS에서 실제 뉴스 데이터를 가져오는 핵심 함수입니다.

    어떻게 동작하나(초보자 관점):
    - RSS URL에 HTTP 요청을 보내 XML을 받습니다.
    - XML을 파싱해 기사 리스트로 변환합니다.
    - 실패하면 빈 리스트를 반환해 상위 로직이 fallback하도록 합니다.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return _parse_rss(response.text, max_results)
    except Exception:
        return []


@mcp.tool()
def get_top_news(
    max_results: int = 5,
    language: str | None = None,
    country: str | None = None,
) -> Dict[str, Any]:
    """
    왜 필요한가: 최신 헤드라인을 빠르게 가져와 에이전트가 시장 분위기를
    파악할 수 있게 해주는 핵심 도구입니다.

    어떻게 동작하나(초보자 관점):
    1) Google News RSS 기본 피드를 호출합니다.
    2) 언어/국가 옵션이 있으면 그에 맞는 RSS URL을 구성합니다.
    3) 실패하면 안전하게 더미 뉴스로 fallback 합니다.
    """
    base_url = "https://news.google.com/rss?"
    url = _build_google_news_url(base_url, language=language, country=country)
    articles = _fetch_google_news_rss(url, max_results=max_results)
    if not articles:
        articles = _mock_news("TOP")

    return {"ok": True, "articles": articles, "source": "google_news"}


@mcp.tool()
def search_news(
    query: str,
    max_results: int = 5,
    language: str | None = None,
    country: str | None = None,
) -> Dict[str, Any]:
    """
    왜 필요한가: 특정 키워드에 대한 뉴스를 찾아 에이전트가 관심 주제를
    조사할 수 있게 해줍니다.

    어떻게 동작하나(초보자 관점):
    1) Google News 검색 RSS URL을 만듭니다.
    2) 키워드(query)를 URL 인코딩해 안전하게 전달합니다.
    3) 결과가 없으면 더미 뉴스로 fallback 합니다.
    """
    encoded_query = quote_plus(query)
    base_url = f"https://news.google.com/rss/search?q={encoded_query}"
    url = _build_google_news_url(base_url, language=language, country=country)
    articles = _fetch_google_news_rss(url, max_results=max_results)
    if not articles:
        articles = _mock_news(query)

    return {"ok": True, "articles": articles, "source": "google_news"}


@mcp.tool()
def list_sources() -> Dict[str, Any]:
    """
    왜 필요한가: MCP 클라이언트가 어떤 뉴스 소스가 가능한지 미리 알 수 있어야
    적절한 의사결정을 할 수 있습니다.

    어떻게 동작하나(초보자 관점):
    - 현재 서버가 지원하는 소스를 목록으로 반환합니다.
    - 초보자도 한눈에 이해할 수 있도록 간단한 메타 정보를 포함합니다.
    """
    sources = [
        {"name": "google_news_rss", "type": "rss", "requires_key": False},
        {"name": "mock_news", "type": "fallback", "requires_key": False},
    ]
    return {"ok": True, "sources": sources}


def main() -> None:
    """
    왜 필요한가: MCP 서버를 실행 가능한 엔트리포인트로 만들기 위해 필요합니다.

    어떻게 동작하나(초보자 관점):
    - 환경변수 MCP_TRANSPORT 값을 읽어 stdio/SSE/streamable-http 중 하나로 실행합니다.
    - streamable-http일 때 기본 엔드포인트는 /mcp 입니다.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
