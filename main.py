import asyncio
import csv
import logging
import os
import re
from typing import Tuple
from urllib.parse import urlparse, parse_qs

from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers

from OpenSSL import crypto
import ssl

logger = logging.getLogger(__name__)


# Global configuration
#USE_SSL = False  # Global flag to control SSL usage
USE_SSL = False


# Global connection pool
CONNECTIONS = {}
TOURNAMENTS = {}

history_path = os.path.join("tournaments")
participants_file = os.path.join("participants", "participants.csv")
round_delay_seconds = 1
n_rounds = 100


def create_self_signed_cert():
    
    # Only create if SSL is enabled and certs don't exist
    if not USE_SSL:
        return
    
    # generate key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    # create cert
    cert = crypto.X509()
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60) 
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # save the key and cert
    with open("cert.pem", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open("key.pem", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))


def get_ssl_context():
    if not USE_SSL:
        return None
        
    if not (os.path.exists("cert.pem") and os.path.exists("key.pem")):
        create_self_signed_cert()
        
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain("cert.pem", "key.pem")
    return ssl_context


def get_history_file(tournament):
  return os.path.join(history_path, f"{tournament}.csv")

def sanitize_inputs(input):
  """
  Basic input sanitization
  """
  s = input.strip()
  # UUID 32 hex chars + 4 dashes should be the max expected length
  # token is 32 alphanunmeric characters
  if len(input) > 36:
    raise ValueError("input too long")
  if not re.match(r'^[a-zA-Z0-9_-]+$', s):
    raise ValueError("Invalid characters in input")

def parse_url(url: str) -> Tuple[str, str]:
  """
  Extracts the tournament and participant from the url
  """
  parsed_url = urlparse(url)
  path = parsed_url.path
  query_params = parse_qs(parsed_url.query)

  tournament = path.split('/')[1]
  participant = query_params.get('participant')[0]

  return tournament, participant


async def process_request(connection, request) -> Response:
  try:
    tournament, participant = parse_url(request.path)
    sanitize_inputs(tournament)
    sanitize_inputs(participant)
  except Exception as e:
    logger.error({
      'message': "Failed to parse url",
      'error': e,
    })
    return Response(400, "Unable to handle request", Headers({}))

  logging.info({
    'message': "Incoming request",
    'tournament': tournament,
    'participant': participant,
  })

  # TODO: Check that tournament exists
  history_filepath = get_history_file(tournament)
  if not os.path.isfile(history_filepath):
    logger.info({
      'message': "Request to join non-existent tournament",
      'tournament': tournament,
      'participant': participant,
    })
    return Response(400, "No tournament", Headers({}))

  # Invalid tournament file will cause an error to be thrown here so there shouldn't be a need to be too strict with tournament input
  pattern = re.compile("^# Participants: \[(?P<a>[a-zA-Z0-9_-]+),(?P<b>[a-zA-Z0-9_-]+)\]$")
  tournament_participants = None
  with open(history_filepath, 'r') as f:
    for line in f:
      if tournament_participants:
        pass
      m = pattern.search(line)
      # Check if both participants are found in line
      if m and m.group('b'):
        tournament_participants = (m.group('a'), m.group('b'))

    # File should not be empty so there's no need to handle that case
    last_line = line
    if last_line == "# COMPLETED":
      return Response(400, "Completed tournament", Headers({}))

  if participant not in tournament_participants:
    return Response(400, "Participant not in tournament", Headers({}))
  
  token = request.headers.get('Authorization')
  sanitize_inputs(token)

  authenticated = False
  with open(participants_file, 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      if participant == row['participant'] and token == row['token']:
        authenticated = True

  if not authenticated:
    return Response(400, "Invalid token", Headers({}))

  return 


async def handler(websocket):
  # Once the websocket connection has been established, the process request handler has already verified the tournament, participant and auth
  tournament, participant = parse_url(websocket.request.path)

  logger.info({
    'message': "Websocket established",
    'tournament': tournament,
    'participant': participant,
  })

  # Register websocket to CONNECTIONS
  if tournament not in CONNECTIONS:
    CONNECTIONS[tournament] = {}
  if participant in CONNECTIONS[tournament]:
    logger.error({
      'message': "Participant already connected to tournament",
      'tournament': tournament,
      'participant': participant,
    })
    return 
  CONNECTIONS[tournament][participant] = websocket

  if tournament not in TOURNAMENTS:
    # Init tournament
    TOURNAMENTS[tournament] = {
      'stage': 'Waiting for players',
      'participants': [],
      'round': 0,
      'state': [None, None],
    }
  if TOURNAMENTS[tournament]['stage'] == 'Waiting for players':
    if participant not in TOURNAMENTS[tournament]['participants']:
      TOURNAMENTS[tournament]['participants'].append(participant)


  try:
    async for message in websocket:
      logger.info({
        'message': "Message received",
        'tournament': tournament,
        'participant': participant,
        'content': message,
      })

      if not tournament in TOURNAMENTS:
        # Tournament has already been closed
        return

      for i, p in enumerate(TOURNAMENTS[tournament]['participants']):
        if participant == p:
          # Input validation to prevent malicious input
          choice = message.strip()
          if choice in ('C', 'B'):
            TOURNAMENTS[tournament]['state'][i] = message
  finally:
    # Handle disconnect
    del CONNECTIONS[tournament][participant]
    if not CONNECTIONS[tournament]:
      del CONNECTIONS[tournament]


async def send(tournament: str, participant: str, message: str):
  try:
    websocket = CONNECTIONS[tournament][participant]
  except KeyError as e:
    logger.error({
      'message': "Connection has been deleted",
      'error': e
    })
    return

  if message is None:
    message = "Forfeit"

  try:
    await websocket.send(message)
  except Exception as e:
    logger.error({
      'message': "Unknown error when sending",
      'tournament': tournament,
      'participant': participant,
      'message': message,
    })


async def main(port: int = 8000):
    # make sure the cert exist
    #if not (os.path.exists("cert.pem") and os.path.exists("key.pem")):
        #create_self_signed_cert()
    
    # configue the SSL
    #ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    #ssl_context.load_cert_chain("cert.pem", "key.pem")

    ssl_context = get_ssl_context()

    # Log to stdout
    logging.basicConfig(handlers=[logging.StreamHandler()], level=logging.INFO)

  # async with serve(handler, "0.0.0.0", port, process_request=process_request):
    async with serve(handler, "0.0.0.0", port, ssl=ssl_context, process_request=process_request):
      while True:
        await asyncio.sleep(round_delay_seconds)
        completed_tournaments = []
        for tournament_uuid, tournament in TOURNAMENTS.items():
          if tournament['stage'] == 'Waiting for players' and len(tournament['participants']) == 2 and None not in tournament['state']:
            with open(get_history_file(tournament_uuid), 'a') as f:
              line = ','.join(tournament['participants'])
              f.write(f"{line}\n")
            tournament['stage'] = 'Started'
          if tournament['stage'] == 'Started':
            state = [s for s in tournament['state']]
            # Write to history
            # This appears to be a bottleneck
            with open(get_history_file(tournament_uuid), 'a') as f:
              # Convert state to comma separated string, replace None with "Forfeit"
              line = ','.join([state if state is not None else "Forfeit" for state in tournament['state']])
              f.write(f"{line}\n")

            # Terminate after n_rounds
            if tournament['round'] >= n_rounds-1:
              with open(get_history_file(tournament_uuid), 'a') as f:
                # No new line to make it easier to find
                f.write(f"# COMPLETED")
              completed_tournaments.append(tournament_uuid)
            else:
              # Reset round
              TOURNAMENTS[tournament_uuid]['state'] = [None, None]
              TOURNAMENTS[tournament_uuid]['round'] += 1

            # Send opponent's choices to participants after the server is ready to recieve new inputs
            await send(tournament_uuid, tournament['participants'][0], state[1])
            await send(tournament_uuid, tournament['participants'][1], state[0])
        for tournament_uuid in completed_tournaments:
          del TOURNAMENTS[tournament_uuid]
          logger.info({
            'message': "Deleted tournament",
            'tournament': tournament_uuid
          })
        completed_tournaments = []
      await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
  asyncio.run(main(8000))
