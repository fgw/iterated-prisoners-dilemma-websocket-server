import asyncio
from websockets.sync.client import connect

from strategies import NaiveStrategy, TitForTatStrategy, RandomStrategy

class Participant:
    def __init__(self, participant, token):
        self.participant = participant
        self.token = token
        self.strategy = None

    def join_tournament(self, host, port, tournament, ssl=False):
        if self.strategy is None:
            raise Exception("Strategy not set")
        protocol = "wss" if ssl == True else "ws"
        with connect(f"{protocol}://{host}:{port}/{tournament}?participant={self.participant}", additional_headers={'authorization': self.token}) as websocket:
            websocket.send("C")
            while True:
                message = websocket.recv()
                print(message)
                message = self.strategy.play(message) 
                websocket.send(message)


if __name__ == "__main__":
    import argparse

    # python participant/websocket_client.py host 443 tournament participant-a token --ssl --strategy random
    parser = argparse.ArgumentParser()

    parser.add_argument('host', type=str)
    parser.add_argument('port', type=int)
    parser.add_argument('tournament', type=str)
    parser.add_argument('participant', type=str)
    parser.add_argument('token', type=str)
    parser.add_argument('--ssl', action='store_true', default=False)
    parser.add_argument('--strategy', type=str, choices=['naive', 'titfortat', 'random'], default='naive')

    args = parser.parse_args()

    participant = Participant(args.participant, args.token)
    
    if args.strategy == 'naive':
        participant.strategy = NaiveStrategy()
    elif args.strategy == 'titfortat':
        participant.strategy = TitForTatStrategy()
    elif args.strategy == 'random':
        participant.strategy = RandomStrategy()

    participant.join_tournament(args.host, args.port, args.tournament, args.ssl)
