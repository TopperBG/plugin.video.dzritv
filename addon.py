import sys
from urllib.parse import parse_qsl, urlencode

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import dzritv


HANDLE = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]


def plugin_url(**query):
    return PLUGIN_URL + "?" + urlencode(query)


def add_directory_item(label, query, info=None):
    item = xbmcgui.ListItem(label=label)
    item.setInfo("video", info or {"title": label})
    xbmcplugin.addDirectoryItem(
        HANDLE,
        plugin_url(**query),
        item,
        isFolder=True,
    )


def add_playable_item(match):
    label = match.title
    if match.start_time:
        label = f"{match.start_time}  {label}"

    item = xbmcgui.ListItem(label=label)
    item.setInfo(
        "video",
        {
            "title": match.title,
            "plot": match.league,
            "genre": match.sport,
        },
    )
    item.setProperty("IsPlayable", "true")

    xbmcplugin.addDirectoryItem(
        HANDLE,
        plugin_url(action="play", url=match.url, title=match.title),
        item,
        isFolder=False,
    )


def show_sports():
    page = dzritv.fetch(dzritv.BASE_URL)
    sports = dzritv.parse_sports(page)

    add_directory_item("All live", {"action": "matches"})
    for sport in sports:
        label = sport.name
        if sport.count is not None:
            label = f"{sport.name} ({sport.count})"
        add_directory_item(label, {"action": "matches", "sport": sport.name})

    xbmcplugin.setContent(HANDLE, "videos")
    xbmcplugin.endOfDirectory(HANDLE)


def show_matches(sport=None):
    page = dzritv.fetch(dzritv.BASE_URL)
    matches = dzritv.parse_matches(page, sport=sport)

    if not matches:
        xbmcgui.Dialog().notification("DZRI TV", "No live matches found", xbmcgui.NOTIFICATION_INFO)

    for match in matches:
        add_playable_item(match)

    xbmcplugin.setContent(HANDLE, "videos")
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def play(match_url, title):
    try:
        stream_url = dzritv.resolve_stream(match_url)
    except dzritv.DzriTvError as exc:
        xbmcgui.Dialog().notification("DZRI TV", str(exc), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    headers = dzritv.playback_headers(match_url)
    item = xbmcgui.ListItem(path=dzritv.with_kodi_headers(stream_url, headers))
    item.setInfo("video", {"title": title})
    item.setMimeType("application/vnd.apple.mpegurl")
    item.setContentLookup(False)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)


def router():
    params = dict(parse_qsl(sys.argv[2][1:]))
    action = params.get("action")

    if action == "matches":
        show_matches(params.get("sport"))
    elif action == "play":
        play(params["url"], params.get("title", "DZRI TV"))
    else:
        show_sports()


if __name__ == "__main__":
    try:
        router()
    except dzritv.DzriTvError as exc:
        xbmcgui.Dialog().notification("DZRI TV", str(exc), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
