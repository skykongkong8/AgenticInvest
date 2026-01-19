from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

import httpx

from src.tools.mcp_client import call_mcp_tool

DEFAULT_PAGE_SIZE = 20
DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp"


def _mock_news(ticker: str) -> List[Dict[str, str]]:
    """
    왜 필요한가: MCP/NewsAPI 연결이 아직 없거나 실패했을 때도 파이프라인이
    끊기지 않도록 최소한의 더미 데이터를 제공해야 합니다.

    어떻게 동작하나(초보자 관점):
    - 티커 문자열을 숫자로 바꿔(seed) 매번 같은 결과가 나오게 만듭니다.
    - seed 값으로 일부 기사만 선택해 일관된 테스트가 가능하도록 합니다.
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


def _normalize_newsapi_article(article: Dict[str, str]) -> Dict[str, str]:
    """
    왜 필요한가: 외부 뉴스 API 응답은 서비스마다 필드명이 달라서,
    이후 단계(요약/리스크 탐지)가 안정적으로 동작하려면 스키마를 통일해야 합니다.

    어떻게 동작하나(초보자 관점):
    - 원본 JSON에서 제목/날짜/요약/출처만 추려서 간단한 딕셔너리로 만듭니다.
    - 부족한 필드는 빈 문자열로 채워 예외를 줄입니다.
    """
    return {
        "title": article.get("title", "").strip(),
        "date": article.get("publishedAt", "").strip(),
        "snippet": (article.get("description") or article.get("content") or "").strip(),
        "source": (article.get("source", {}) or {}).get("name", "").strip(),
        "sentiment": "neutral",
    }


def _fetch_news_from_newsapi(ticker: str, days: int) -> List[Dict[str, str]]:
    """
    왜 필요한가: MCP 서버를 쓰지 않더라도 실제 뉴스를 가져올 기본 경로가 필요합니다.

    어떻게 동작하나(초보자 관점):
    - 환경변수에 설정된 API 키로 NewsAPI에 HTTP 요청을 보냅니다.
    - 응답 JSON에서 기사 목록을 꺼내 표준 스키마로 변환합니다.
    - 실패 시 빈 목록을 돌려서 상위 로직이 fallback을 결정할 수 있게 합니다.
    """
    api_key = os.getenv("NEWS_API_KEY", "").strip()
    if not api_key:
        return []

    base_url = os.getenv("NEWS_API_BASE_URL", "https://newsapi.org/v2/everything").strip()
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "q": ticker,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": DEFAULT_PAGE_SIZE,
        "apiKey": api_key,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(base_url, params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return []

    articles = payload.get("articles", []) if isinstance(payload, dict) else []
    return [_normalize_newsapi_article(a) for a in articles if isinstance(a, dict)]


def _normalize_mcp_article(article: Dict[str, Any]) -> Dict[str, str]:
    """
    왜 필요한가: MCP 서버의 응답은 도구 구현에 따라 필드명이 다를 수 있어,
    downstream 로직이 깨지지 않도록 스키마를 통일해야 합니다.

    어떻게 동작하나(초보자 관점):
    - title/date/snippet/source 같은 핵심 필드를 안전하게 뽑아냅니다.
    - 누락된 값은 빈 문자열로 처리해 예외를 줄입니다.
    """
    return {
        "title": str(article.get("title", "")).strip(),
        "date": str(article.get("published", "") or article.get("date", "")).strip(),
        "snippet": str(article.get("snippet", "") or article.get("description", "")).strip(),
        "source": str(article.get("source", "")).strip(),
        "sentiment": str(article.get("sentiment", "neutral")).strip(),
        "url": str(article.get("link", "") or article.get("url", "")).strip(),
    }


def _fetch_news_via_mcp(ticker: str, days: int) -> tuple[List[Dict[str, str]], bool]:
    """
    왜 필요한가: 에이전트가 MCP 기반 도구를 통해 뉴스 공급자를 교체할 수 있도록
    표준 인터페이스를 제공해야 합니다.

    어떻게 동작하나(초보자 관점):
    - MCP 서버 URL 또는 실행 커맨드를 환경변수에서 읽습니다.
    - README에 정의된 도구(get_top_news/search_news)를 호출해 구조화된 결과를 받습니다.
    - 호출 자체가 실패하면 False를 반환해 상위 로직이 다른 경로로 fallback하도록 합니다.
    """
    mcp_url = os.getenv("MCP_NEWS_URL", DEFAULT_MCP_URL).strip()
    mcp_command = os.getenv("MCP_NEWS_COMMAND", "").strip()
    mcp_args = os.getenv("MCP_NEWS_ARGS", "").strip()
    search_tool = os.getenv("MCP_NEWS_SEARCH_TOOL", "search_news").strip()
    top_tool = os.getenv("MCP_NEWS_TOP_TOOL", "get_top_news").strip()
    language = os.getenv("MCP_NEWS_LANGUAGE", "").strip() or None
    country = os.getenv("MCP_NEWS_COUNTRY", "").strip() or None
    max_results = int(os.getenv("MCP_NEWS_MAX_RESULTS", str(DEFAULT_PAGE_SIZE)))

    if not mcp_url and not mcp_command:
        return [], False

    if ticker and ticker != "UNKNOWN":
        tool_name = search_tool
        arguments = {"query": ticker, "max_results": max_results, "language": language, "country": country}
    else:
        tool_name = top_tool
        arguments = {"max_results": max_results, "language": language, "country": country}

    try:
        result = call_mcp_tool(
            tool_name=tool_name,
            arguments=arguments,
            server_url=mcp_url or None,
            server_command=mcp_command or None,
            server_args=mcp_args or None,
        )
    except Exception:
        return [], False

    if not isinstance(result, dict):
        return [], False

    articles = result.get("articles") or result.get("items") or result.get("results")
    if isinstance(articles, list):
        normalized = [_normalize_mcp_article(a) for a in articles if isinstance(a, dict)]
        return normalized, True

    return [], True


def fetch_news(ticker: str, days: int = 7) -> List[Dict[str, str]]:
    """
    왜 필요한가: 뉴스 수집은 Agent의 의사결정 근거가 되므로, 항상 일관된 방식으로
    데이터를 제공해야 합니다.

    어떻게 동작하나(초보자 관점):
    1) MCP가 설정되어 있으면 MCP 도구를 먼저 호출합니다.
    2) MCP가 없거나 실패하면 NewsAPI를 직접 호출합니다.
    3) 모든 경로가 실패하면 마지막으로 모킹 데이터를 반환합니다.
    """
    mcp_articles, used_mcp = _fetch_news_via_mcp(ticker, days)
    if used_mcp:
        return mcp_articles

    newsapi_articles = _fetch_news_from_newsapi(ticker, days)
    if newsapi_articles:
        return newsapi_articles

    return _mock_news(ticker)
