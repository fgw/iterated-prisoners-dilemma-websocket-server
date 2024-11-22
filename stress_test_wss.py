import asyncio
import websockets
import random
import csv
import os
import ssl
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def play_game(url: str, tournament_id: str, participant: str, token: str) -> None:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        headers = {'authorization': token}
        async with websockets.connect(
            f"{url}/{tournament_id}?participant={participant}",
            ssl=ssl_context,
            additional_headers=headers
        ) as websocket:
            await websocket.send("C")
            logger.info(f"{participant}: Connected and sent initial move")
            
            while True:
                message = await websocket.recv()
                choice = random.choice(("C", "B"))
                await websocket.send(choice)
                logger.info(f"{participant}: Received {message}, sent {choice}")
    except Exception as e:
        logger.error(f"Error for {participant}: {str(e)}")
        raise

def read_participants() -> Dict[str, str]:
    participants = {}
    csv_path = os.path.join('participants', 'participants.csv')
    
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            participants[row[0]] = row[1]
            logger.info(f"Reading participant: {row[0]}, Token: {row[1][:8]}...")
    return participants

def read_tournament_pairs() -> List[Tuple[str, str, str]]:
    pairs = []
    with open('tournament_records.txt', 'r') as f:
        for line in f:
            tournament_id, p1, p2 = line.strip().split(',')
            pairs.append((tournament_id, p1, p2))
            logger.info(f"Match pairing: {p1} vs {p2}, Tournament ID: {tournament_id}")
    return pairs

async def main():
    url = "wss://127.0.0.1:8000"
    logger.info("Starting to read participant information...")
    participants = read_participants()
    logger.info(f"Total participants read: {len(participants)}")
    
    logger.info("Starting to read match pairings...")
    tournament_pairs = read_tournament_pairs()
    logger.info(f"Total match pairings read: {len(tournament_pairs)}")
    
    participant_count = len(participants)
    if participant_count % 2 != 0:
        participant_count -= 1
        logger.warning(f"Odd number of participants ({participant_count + 1}). Last group will not participate.")
    
    tasks = []
    for tournament_id, p1, p2 in tournament_pairs[:participant_count//2]:
        tasks.extend([
            play_game(url, tournament_id, p1, participants[p1]),
            play_game(url, tournament_id, p2, participants[p2])
        ])
    
    logger.info(f"Starting {len(tasks)} game tasks")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Program error: {str(e)}")
