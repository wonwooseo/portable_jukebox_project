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
                let player_type = msg['type'];
                if(player_type === 'file') {
                    document.getElementById('cover').src = '/static/img/cover_cache/' + msg['title'] + '.png';
                    document.getElementById('cover').onerror = function () {
                        this.src = '/static/img/default.png';
                    };
                }
                else {
                    document.getElementById('cover').src = '/static/img/default_net.png';
                }
                document.getElementById('title').innerText = msg['title'];
                document.getElementById('artist').innerText = msg['artist'];
                document.getElementById('album').innerText = msg['album'];
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