# portable_jukebox_project
Project to build a locally-hosted, portable jukebox application based on Django.

## Features
- Clients add music to playlist, from youtube or file
- Now playing page with cover art
- Skip, re-add vote
    - Settings for minimum votes

## Blueprint (views)
- [x] /index
- [x] /nowplaying
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
        - [ ] Client picks from results
    - [x] Client clicks add from file
        - [ ] Client picks from cache
        - [ ] Client uploads own file
- [ ] Client clicks skip button
- [ ] Client clicks re-add button
- [ ] Skip condition is met
- [ ] Re-add condition is met

## Notes for personal use
- how to check youtube video duration
- embedding youtube player
- how to signal end of song / skip
- django.channels / websockets for client-server communication
    - skip, re-add, playlist update?
- Album cover retrieving code
    ```python
    import stagger.id3
    tag = stagger.read_tag('music_cache/a.mp3')  # get tags of music file
    cover = None
    with tag.get(stagger.id3.PIC) as ptag:
        if ptag:
            cover = ptag[0].data
    with tag.get(stagger.id3.APIC) as aptag:
        if aptag:
            cover = aptag[0].data
    # if cover left None, no album cover in tag
    ```