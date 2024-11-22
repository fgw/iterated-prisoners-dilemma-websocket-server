from websockets.sync.client import connect
import random
import ssl

# Parameters will be issued during the tournament 
url = "wss://127.0.0.1:8000"
tournament = "aad7b16a-4835-4955-8960-23aa8309007a"
participant = "group1"
token = "spKSK6WusvVb5GYxJl3WiwaYABbPfxV4"

# Create SSL context that doesn't verify certificate
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Connect to websocket server with SSL context
with connect(
    f"{url}/{tournament}?participant={participant}", 
    additional_headers={'authorization': token},
    ssl_context=ssl_context
) as websocket:
    # Once connected, immediately send your first choice
    # The choice only accepts "C" (Collaborate) or "B" (Betray)
    # Any other choices forfiets the round
    websocket.send("C")
    while True:
        # You will recieve the opponent's last choice from the server when the round is over
        # This will be a "C" or "B"
        message = websocket.recv()
        # Your strategy here:
        choice = random.choice(("C", "B"))
        
        # Send your choice within the time limit or you will forfiet the round
        websocket.send(choice)
