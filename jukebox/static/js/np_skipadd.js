/**
 * Script to handle websocket events for skip / re-add
 */
$(document).ready(function() {
    let idx;
    let sa_socket = new WebSocket('ws://' + window.location.host + '/ws/skipadd/');

    sa_socket.onopen = function(f) {
        console.info('Opened skip-add socket');
        sa_socket.send(JSON.stringify({
            'fetch': 'request',
        }));
    };

    sa_socket.onclose = function(f) {
        console.error('Skip-add socket closed');
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
                idx = msg['idx'];
                scount_elem.innerText = msg['skip'];
                rcount_elem.innerText = msg['readd'];
                if(msg['readd'] === '✔') document.getElementById('btn_readd').disabled = true;
                break;
            case 'notplaying':
                let skipbtn_elem = document.getElementById('btn_skip');
                skipbtn_elem.disabled = true;
                let readdbtn_elem = document.getElementById('btn_readd');
                readdbtn_elem.disabled = true;
                break;
            default:
                console.error('Invalid target embedded in message');
        }
    };

    let skipbtn_elem = document.getElementById('btn_skip');
    skipbtn_elem.onclick = function(f) {
        sa_socket.send(JSON.stringify({
            'target': 'skip',
            'action': 'plus',
            'idx': idx,
        }));
        skipbtn_elem.firstElementChild.innerText = 'Voted';
        skipbtn_elem.disabled = true;
    };

    let readdbtn_elem = document.getElementById('btn_readd');
    readdbtn_elem.onclick = function(f) {
        sa_socket.send(JSON.stringify({
            'target': 'readd',
            'action': 'plus',
            'idx': idx,
        }));
        readdbtn_elem.firstElementChild.innerText = 'Voted';
        readdbtn_elem.disabled = true;
    };
});