from websockets.sync.client import connect
import random

# Parameters will be issued during the tournament
url = "ws://ec2-18-143-47-19.ap-southeast-1.compute.amazonaws.com:8000"
tournament = "f00c2bd8-793c-4eba-a6c1-ee5589470b76"
participant = "grouptest2"
token = "L9qms8bwXFTmQ5oa621gBl4U4ifHM2kW"

# grouptest1 vs grouptest2: f00c2bd8-793c-4eba-a6c1-ee5589470b76
# grouptest1	WmLVWUgnNjwrIl5KaK0IRNqCApL6ujNl
# grouptest2	L9qms8bwXFTmQ5oa621gBl4U4ifHM2kW
# host  ec2-18-143-47-19.ap-southeast-1.compute.amazonaws.com
# port 8000

# Connect to websocket server
with connect(f"{url}/{tournament}?participant={participant}", additional_headers={'authorization': token}) as websocket:
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
        websocket.send(message)