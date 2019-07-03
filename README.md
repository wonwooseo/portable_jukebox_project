# portable_jukebox_project
Project to build a locally-hosted, portable jukebox application based on Django.

## Features
- Clients add music to playlist, from youtube or file
- Now playing page with cover art
- Skip, re-add vote
    - Settings for minimum votes

## Core dev env
- Python 3.7
- Django v2.2.1
- Django Channels v2.1.7
- redis (running on docker container)

## Testing
- Selenium

## Blueprint (views)
- [x] /index
- [x] /nowplaying
- [x] /host_player
- [x] /qrcode
- [x] /add
- [x] /add_youtube
- [x] /search_youtube
- [x] /add_youtube_item
- [x] /add_file
- [x] /add_file_item
- [x] /add_success
- [x] /add_error

## Blueprint (UCs)
- [x] Host starts the server
- [x] Client accesses server
- [x] Client enters session password
- [x] Client clicks 'how to access..' button
- [x] Client clicks add button
    - [x] Client clicks add from youtube
        - [x] Client searches keyword
        - [x] Client picks from results
    - [x] Client clicks add from file
        - [x] Client picks from cache
        - [x] Client uploads own file
- [x] Client clicks skip button
- [x] Client clicks re-add button
- [x] Skip condition is met
- [x] Re-add condition is met

## Notes for personal use
- how to check youtube video duration
- channels use docker/redis for broadcast backend..
    - find other lightweight options (for production)
    - or manually keep channel names in consumers.py
- Configure host IP automatically
- remove PlaylistItem.playing field