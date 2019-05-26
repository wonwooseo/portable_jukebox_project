/**
 *  Script to handle events from music websocket
 */

// Global scope variables (for use in iframe api event functions)
var path;
var m_socket;

$(document).ready(function() {
    m_socket = new WebSocket('ws://' + window.location.host + '/ws/music/');
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
                path = msg['link'];
                if(player_type === 'file') {
                    // clear placeholding div
                    let div = document.getElementById('player_dom');
                    div.parentElement.removeChild(div);
                    // create html5 audio player
                    let html5player = document.createElement('audio');
                    html5player.setAttribute('src', path);
                    html5player.setAttribute('controls', '');
                    html5player.setAttribute('autoplay', '');
                    html5player.volume = 0.25;
                    html5player.onended = function() {
                      m_socket.send(JSON.stringify({
                          'target': 'skip',
                      }));
                    };
                    document.getElementById('player_area').appendChild(html5player);
                }
                else {
                    // load Youtube Iframe API script
                    let tag = document.createElement('script');
                    tag.src = 'https://youtube.com/iframe_api';
                    document.getElementById('player_area').appendChild(tag);
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

var player;
function onYouTubeIframeAPIReady() {
    // replace div with iframe when api is ready
    console.info('IframeAPI ready');
    player = new YT.Player('player_dom', {
        height: '480',
        width: '640',
        videoId: path,
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function onPlayerReady(event) {
    // Start playing when ready
    event.target.playVideo();
}

function onPlayerStateChange(event) {
    // Send skip signal when video ends
    if (event.data == YT.PlayerState.ENDED) {
        m_socket.send(JSON.stringify({
            'target': 'skip',
        }));
    }
}