/**
 * Script to handle websocket events for skip / re-add in host_player
 */
$(document).ready(function() {
    let sa_socket = new WebSocket('ws://' + window.location.host + '/ws/skipadd/');
    sa_socket.onopen = function(f) {
        console.info('Opened skip-add socket');
        sa_socket.send(JSON.stringify({
            'fetch': 'request',
        }));
    };

    sa_socket.onclose = function(f) {
        $('#socket_close_alert').modal({
            backdrop: 'static'
        })
    };

    sa_socket.onmessage = function(f) {
        let msg = JSON.parse(f.data);
        let target = msg['target'];
        switch(target) {
            case 'skip':
                document.getElementById('skip_count').innerText = msg['count'];
                break;
            case 'readd':
                document.getElementById('readd_count').innerText = msg['count'];
                break;
            case 'fetch':
                let scount_elem = document.getElementById('skip_count');
                let rcount_elem = document.getElementById('readd_count');
                scount_elem.innerText = msg['skip'];
                rcount_elem.innerText = msg['readd'];
                break;
            case 'notplaying':
                break;
            default:
                console.error('Invalid target embedded in message');
        }
    };
});