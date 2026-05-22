from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from resources.lib import dzritv


SAMPLE = """
<div class="sport_matches_desk">
  <span class="txt_on_border">Soccer (2)</span>
  <div class="league">Latvia. Higher League.</div>
  <div class="football_desk desc_item">
    <a href="/match/auda-riga-fc-liepaja-24399532">
      <div class="txt_date_time">2026-05-22 19:00</div>
      <div class="matches">Auda Riga - FC Liepaja</div>
      <div class="live"><span>VIEW ONLINE</span></div>
    </a>
  </div>
</div>
<div class="sport_matches_desk">
  <span class="txt_on_border">Basketball (1)</span>
  <div class="league">Euroleague</div>
  <div class="football_desk desc_item">
    <a href="/match/olympiacos-fenerbahce-24399526">
      <div class="txt_date_time">2026-05-22 19:00</div>
      <div class="matches">Olympiacos - Fenerbahce</div>
      <div class="live"><span>VIEW ONLINE</span></div>
    </a>
  </div>
</div>
<div class="footer"></div>
"""


def test_parse_sports():
    sports = dzritv.parse_sports(SAMPLE)
    assert sports == [dzritv.Sport("Soccer", 2), dzritv.Sport("Basketball", 1)]


def test_parse_matches_by_sport():
    matches = dzritv.parse_matches(SAMPLE, sport="Soccer")
    assert len(matches) == 1
    assert matches[0].title == "Auda Riga - FC Liepaja"
    assert matches[0].league == "Latvia. Higher League."
    assert matches[0].url == "https://dzritv.com/match/auda-riga-fc-liepaja-24399532"


def test_resolve_stream_pattern():
    page = "var videoSrc = 'https://example.test/live/playlist.m3u8?token=1';"
    assert dzritv.resolve_stream_from_page(page) == "https://example.test/live/playlist.m3u8?token=1"


def test_kodi_header_suffix_is_urlencoded():
    url = "https://example.test/live/playlist.m3u8?token=1"
    headers = {
        "User-Agent": "Mozilla/5.0 Test",
        "Referer": "https://dzritv.com/match/example",
    }

    assert dzritv.with_kodi_headers(url, headers) == (
        "https://example.test/live/playlist.m3u8?token=1|"
        "User-Agent=Mozilla%2F5.0+Test&Referer=https%3A%2F%2Fdzritv.com%2Fmatch%2Fexample"
    )
