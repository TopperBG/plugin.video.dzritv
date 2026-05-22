# DZRI TV Kodi Add-on

Kodi video plugin for browsing live streams from `https://dzritv.com/`.

## Features

- Lists live sport categories from the DZRI TV home page.
- Filters matches by selected sport.
- Resolves the current HLS `.m3u8` URL only when playback starts, because DZRI TV signs stream URLs for a short time.

## Install

Zip the `plugin.video.dzritv` directory and install it in Kodi through:

`Settings -> Add-ons -> Install from zip file`

Example:

```bash
zip -r plugin.video.dzritv-0.1.0.zip plugin.video.dzritv -x '*/tests/*'
```

## Development Check

```bash
python3 -m pytest plugin.video.dzritv/tests
python3 -m compileall -q plugin.video.dzritv
```
