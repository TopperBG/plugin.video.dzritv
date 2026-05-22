import html
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://dzritv.com/"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/124.0 Safari/537.36"
)


class DzriTvError(Exception):
    pass


@dataclass(frozen=True)
class Sport:
    name: str
    count: Optional[int] = None


@dataclass(frozen=True)
class Match:
    title: str
    url: str
    sport: str
    league: str = ""
    start_time: str = ""


def fetch(url: str, timeout: int = 15) -> str:
    request = Request(
        urljoin(BASE_URL, url),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except OSError as exc:
        raise DzriTvError(f"Could not load DZRI TV: {exc}") from exc


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def absolute_url(url: str) -> str:
    return urljoin(BASE_URL, html.unescape(url))


def _sport_from_heading(section: str) -> Optional[Sport]:
    match = re.search(r'<span[^>]+class="txt_on_border"[^>]*>(.*?)</span>', section, re.S)
    if not match:
        return None

    heading = clean_text(match.group(1))
    count_match = re.search(r"\((\d+)\)\s*$", heading)
    count = int(count_match.group(1)) if count_match else None
    name = re.sub(r"\s*\(\d+\)\s*$", "", heading).strip()
    if not name:
        return None
    return Sport(name=name, count=count)


def _match_sections(page: str) -> Iterable[str]:
    marker = '<div class="sport_matches_desk"'
    starts = [match.start() for match in re.finditer(re.escape(marker), page)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else page.find('<div class="footer"', start)
        if end == -1:
            end = len(page)
        yield page[start:end]


def parse_sports(page: str) -> List[Sport]:
    sports: List[Sport] = []
    seen = set()
    for section in _match_sections(page):
        sport = _sport_from_heading(section)
        if sport and sport.name not in seen:
            sports.append(sport)
            seen.add(sport.name)
    return sports


def _parse_match_body(url: str, body: str, sport: str, league: str) -> Optional[Match]:
    title_match = re.search(r'<div[^>]+class="matches"[^>]*>(.*?)</div>', body, re.S)
    if not title_match:
        return None

    time_match = re.search(r'<div[^>]+class="txt_date_time"[^>]*>(.*?)</div>', body, re.S)
    title = clean_text(title_match.group(1))
    if not title:
        return None

    return Match(
        title=title,
        url=absolute_url(url),
        sport=sport,
        league=league,
        start_time=clean_text(time_match.group(1)) if time_match else "",
    )


def parse_matches(page: str, sport: Optional[str] = None) -> List[Match]:
    matches: List[Match] = []
    wanted = sport.casefold() if sport else None

    for section in _match_sections(page):
        current_sport = _sport_from_heading(section)
        if not current_sport:
            continue
        if wanted and current_sport.name.casefold() != wanted:
            continue

        current_league = ""
        token_pattern = re.compile(
            r'<div\s+class="league"[^>]*>(?P<league>.*?)</div>'
            r'|<div[^>]+class="football_desk desc_item"[^>]*>\s*'
            r'<a\s+href="(?P<url>[^"]+)">(?P<body>.*?)(?='
            r'<div\s+class="league"'
            r'|<div[^>]+class="football_desk desc_item"'
            r'|</div>\s*<div\s+class="container"'
            r'|$)',
            re.S,
        )
        for token in token_pattern.finditer(section):
            if token.group("league") is not None:
                current_league = clean_text(token.group("league"))
                continue
            match = _parse_match_body(token.group("url"), token.group("body"), current_sport.name, current_league)
            if match:
                matches.append(match)

    return matches


def resolve_stream_from_page(page: str) -> str:
    patterns = (
        r"videoSrc\s*=\s*'([^']+\.m3u8[^']*)'",
        r'videoSrc\s*=\s*"([^"]+\.m3u8[^"]*)"',
        r'(https?://[^"\']+\.m3u8[^"\']*)',
    )
    for pattern in patterns:
        match = re.search(pattern, page)
        if match:
            return html.unescape(match.group(1))
    raise DzriTvError("No playable stream found for this match")


def resolve_stream(match_url: str) -> str:
    return resolve_stream_from_page(fetch(match_url))


def playback_headers(match_url: str) -> Dict[str, str]:
    parsed = urlparse(match_url)
    referer = f"{parsed.scheme}://{parsed.netloc}{parsed.path}" if parsed.scheme else BASE_URL
    return {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Origin": BASE_URL.rstrip("/"),
    }


def with_kodi_headers(url: str, headers: Dict[str, str]) -> str:
    header_blob = urlencode(headers)
    return f"{url}|{header_blob}" if header_blob else url
