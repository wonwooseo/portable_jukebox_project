#portable_jukebox_project
Project to build a locally-hosted, portable jukebox application based on Django.

##Features
- Clients add music to playlist, from youtube or file
- Now playing page with cover art
- Skip, re-add vote
    - Settings for minimum votes

##Blueprint (views)
- [x] /index
- [x] /nowplaying
- [x] /qrcode
- [ ] /add
- [ ] /add_youtube
- [ ] /add_file
- [ ] /add_result

##Blueprint (UCs)
- [x] Host starts the server
- [x] Client accesses server
- [x] Client enters session password
- [x] Client clicks 'how to access..' button
- [ ] Client clicks add button
    - [ ] Client clicks add from youtube
        - [ ] Client searches keyword
        - [ ] Client picks from results
    - [ ] Client clicks add from file
        - [ ] Client picks from cache
        - [ ] Client uploads own file
- [ ] Client clicks skip button
- [ ] Client clicks re-add button
- [ ] Skip condition is met
- [ ] Re-add condition is met

## Notes for personal use
- How clients find host?
    - QR code?
    - auto detection?
- Set session password at config file
    - option to not use password
- django.channels / websockets for client-server communication
- YouTube Search API
- File transferring logic
- limit access to /host_player
    - based on IP => REMOTE_ADDR
    - set admin password?
