<script>
            const roomName = JSON.parse(document.getElementById('room-name').textContent);
            var chatSocket  = require('./room');
            var chatSocket = new WebSocket(
                'ws://'
                + window.location.host
                + '/ws/adminchat/'
                + roomName
                + '/'
            );

            chatSocket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                document.querySelector('#chat-log').value += (data.message + '\n');
                if (data.message_type === 'button') {
                var btn = document.createElement("BUTTON");
                var t = document.createTextNode("Sample Text");
                btn.appendChild(t);
                btn.setAttribute("style","font-size:14px;background-color: #4CAF50");
                document.body.appendChild(btn);
                // document.getElementById("chat-log").appendChild(btn);
                // btn.innerHTML="<INPUT onclick=\"OnQuery()\" type=\"button\" value=\" Search \" name=\"querybtn\" />";
                console.log('Created Button!');
                }
            };

            chatSocket.onclose = function(e) {
                console.error('Chat socket closed unexpectedly');
                if (is_admin === true) {
                  is_admin = false;
                }
            };

            document.querySelector('#chat-message-input').focus();
            document.querySelector('#chat-message-input').onkeyup = function(e) {
                if (e.keyCode === 13) {  // enter, return
                    document.querySelector('#chat-message-submit').click();
                }
            };

            document.querySelector('#chat-message-submit').onclick = function(e) {
                const messageInputDom = document.querySelector('#chat-message-input');
                const message = messageInputDom.value;
                chatSocket.send(JSON.stringify({
                    'message': message
                }));
                messageInputDom.value = '';
            };
        </script>