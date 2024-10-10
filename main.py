import asyncio
import logging
from typing import Tuple
from urllib.parse import urlparse, parse_qs

from websockets.asyncio.server import serve


logger = logging.getLogger(__name__)


# Global connection pool
CONNECTIONS = {}


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


async def process_request(connection, request):
  logging.info({
    'message': "Incoming request",
    'request': request,
    'path': request.path,
    'headers': request.headers
  })

  try:
    tournament, participant = parse_url(request.path)
  except Exception as e:
    logger.error({
      'message': "Failed to parse url",
      'error': e,
    })
    return 400

  # TODO: Check that tournament exists
  # TODO: Check that participant is part of the tournament

  token = request.headers.get('Authorization')

  # TODO: Check that token is valid for participant

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
  if CONNECTIONS[tournament] is None:
    CONNECTIONS[tournament] = {}
  CONNECTIONS[tournament][participant] = websocket

  try:
    async for message in websocket:
      logger.info({
        'message': "Message received",
        'websocket': websocket,
        'content': message,
      })
  finally:
    # Handle disconnect
    del CONNECTIONS[tournament][participant]
    if not CONNECTIONS[tournament]:
      del CONNECTIONS[tournament]


async def send(tournament: str, participant: str, message: str):
  websocket = CONNECTIONS[tournament][participant]
  await websocket.send(message)


# TODO: Implement game


async def main(port: int = 8000):
  # Log to stdout
  logging.basicConfig(handlers=[logging.StreamHandler()], level=logging.INFO)

  async with serve(handler, "localhost", port, process_request=process_request):
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
  asyncio.run(main(8000))

