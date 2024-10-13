import os
import csv
import secrets
import string


def generate_token(length=32):
    # Define the characters to use: uppercase, lowercase, and digits
    characters = string.ascii_letters + string.digits
    # Generate a secure random token
    token = ''.join(secrets.choice(characters) for _ in range(length))
    return token



if __name__ == "__main__":
  participants_file = os.path.join("participants", "participants.csv")

  out_rows = []

  # Open the existing CSV file for reading
  with open(participants_file, mode='r', newline='') as infile:
      reader = csv.DictReader(infile)
      fieldnames = reader.fieldnames 

      if 'token' not in fieldnames:
        fieldnames + ['token'] 

      # Read and modify each row
      for index, row in enumerate(reader):
          row['token'] = generate_token()  # Add new data
          out_rows.append(row)

  # Write the modified data to a new CSV file
  with open(participants_file, mode='w', newline='') as outfile:
      writer = csv.DictWriter(outfile, fieldnames=fieldnames)
      writer.writeheader()  # Write header
      writer.writerows(out_rows)  # Write all modified rows