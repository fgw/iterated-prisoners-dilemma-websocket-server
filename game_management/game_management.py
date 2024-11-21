import os
import logging

logger = logging.getLogger(__name__)

TOURNAMENTS = {}


def collect_csv_files(folder_path):
    """
    Collects all CSV files in the specified folder and returns their paths in a list.

    Parameters:
    folder_path (str): The path of the folder to search for CSV files.

    Returns:
    list: A list of paths to CSV files.
    """
    csv_files = []

    # Check if the provided path is a directory
    if not os.path.isdir(folder_path):
        logger.exception(f"The provided path '{folder_path}' is not a valid directory.")
        return csv_files

    # Iterate through the folder
    for filename in os.listdir(folder_path):
        # Check if the file has a .csv extension
        if filename.endswith(".csv"):
            # Construct full file path
            full_path = os.path.join(folder_path, filename)
            csv_files.append(filename)

    return csv_files


def populate_tournaments(folder_path):
    file_name_list = collect_csv_files(folder_path)

    tournaments = {}

    for file_name in file_name_list:
        tokens = file_name.replace(".csv", "").split("_")
        if len(tokens) != 3:
            logger.warn(f"Unsupported file name: ({file_name}) found")
            continue

        tournaments = {**tournaments, **{tokens[0]: [tokens[1], tokens[2]]}}
    TOURNAMENTS = tournaments
    return files


def get_players(tournament_id):
    if tournament_id not in TOURNAMENTS:
        return {}
    players = TOURNAMENTS.get(tournament_id)

    tournament_file_name = f"{tournament_id}_{players[0]}_{players[1]}.csv"
    
