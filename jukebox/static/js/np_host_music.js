/**
 *  Script to handle events from music websocket
 */
$(document).ready(function() {
    let m_socket = new WebSocket('ws://' + window.location.host + '/ws/music/');

    m_socket.onopen = function(f) {
        console.info('Opened music socket');
        m_socket.send(JSON.stringify({
            'fetch': 'request',
        }));
    };

    m_socket.onclose = function(f) {
        console.error('music socket closed');
    };

    m_socket.onmessage = function(f) {
        let msg = JSON.parse(f.data);
        let target = msg['target'];
        switch(target) {
            case 'fetch':
                document.getElementById('title').innerText = msg['title'];
                document.getElementById('artist').innerText = msg['artist'];
                document.getElementById('album').innerText = msg['album'];
                let player_type = msg['type'];
                let path = msg['link'];
                console.info(path);
                if(player_type === 'file') {
                    let html5player = document.createElement('audio');
                    html5player.setAttribute('src', path);
                    html5player.setAttribute('controls', '');
                    html5player.setAttribute('autoplay', '');
                    document.getElementById('player_area').appendChild(html5player);
                }
                else {
                    let iframe = document.createElement('iframe');
                    iframe.setAttribute('type', 'text/html');
                    iframe.setAttribute('width', '640');
                    iframe.setAttribute('height', '480');
                    iframe.setAttribute('src', path);
                    iframe.setAttribute('frameborder', '0');
                    iframe.setAttribute('allow', 'autoplay');
                    document.getElementById('player_area').appendChild(iframe);
                }
                break;
            case 'skip':
                location.reload(); //should force full refresh?
                document.documentElement.scrollTop = 0;
                document.body.scrollTop = 0;
                break;
            case 'notplaying':
                document.getElementById('title').innerText = 'No music playing now..';
                document.getElementById('artist').innerText = '';
                document.getElementById('album').innerText = '';
                break;
            default:
                console.error('Invalid target embedded in message');
        }
    };
});