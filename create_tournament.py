import os
import uuid
import datetime 
import pytz

def append_to_record(tournament_uuid, a, b):
    record_file = 'tournament_records.txt'
    with open(record_file, 'a') as f:
        f.write(f"{tournament_uuid},{a},{b}\n")


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  
  parser.add_argument('participants', type=str, nargs=2 )

  args = parser.parse_args()

  a, b = args.participants

  history_dir_path = 'tournaments'

  # Create a UUID version 4
  tournament_uuid = uuid.uuid4()
  history_file_path = os.path.join(history_dir_path, f"{tournament_uuid}.csv")
  # Regenerate tournament uuid if there is already another tournament with the same uuid
  while os.path.isfile(history_file_path):
    tournament_uuid = uuid.uuid4()
    history_file_path = os.path.join(history_dir_path, f"{tournament_uuid}.csv")

  with open(history_file_path, 'w') as f:
    # Add current time to file
    dt = datetime.datetime.now(pytz.timezone("Asia/Singapore")) 
    current_time_str = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    f.write(f"# {current_time_str}\n")
    f.write(f"# Participants: [{a},{b}]\n")

  append_to_record(tournament_uuid, a, b)
