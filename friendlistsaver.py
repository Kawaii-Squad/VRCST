import os
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import requests
import time  # Import the time module for sleep

def choose_friendlist_backup():
    try:
        # Create a Tkinter window
        root = tk.Tk()
        root.withdraw()  # Hide the main Tkinter window

        # Path to the folder containing the friend list backups
        folder_path = os.path.join(os.path.expanduser("~"), "VRCST", "LocalDB", "info")

        # Show an information message with messagebox
        messagebox.showinfo("Backup Selection", "Please choose a friend list backup in the folder VRCST/LocalDB/info")

        # Ask the user to select a file
        file_path = filedialog.askopenfilename(initialdir=folder_path,
                                               title="Choose a friend list backup",
                                               filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")])

        if not file_path:
            print("No file selected.")
            return None
        
        return file_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def execute_friend_requests(file_path, auth_cookie):
    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            print(f"The specified file does not exist: {file_path}")
            return

        # Read the content of the file as binary
        with open(file_path, 'rb') as file:
            content = file.read()

        # Decode the content assuming UTF-8 encoding
        try:
            data = json.loads(content.decode('utf-8'))
        except UnicodeDecodeError:
            print("Failed to decode file content as UTF-8. Attempting to decode with 'latin-1' encoding.")
            data = json.loads(content.decode('latin-1'))

        # Iterate through each entry in the JSON array
        for entry in data:
            # Check if 'id' key exists in the entry
            if "id" in entry:
                user_id = entry["id"]
                # Send a friend request via requests module with headers
                url = f"https://vrchat.com/api/1/user/{user_id}/friendRequest"
                headers = {
                    "User-Agent": user_agent,  # Use the provided user agent
                    "Cookie": f"auth={auth_cookie}"
                }
                response = requests.post(url, headers=headers)
                print(f"Sent friend request to {user_id}. Response: {response.text}")

                # Wait for 3 minutes before sending the next request
                time.sleep(180)
            else:
                print(f"Skipping entry: No 'id' key found in entry {entry}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Constants
AUTH_COOKIE_PATH = 'LocalDB/temps/AuthCookie.txt'
user_agent = 'VRCST / Kawaii Squad Studio'  # Ensure user_agent is defined

# Function to get authentication cookie
def get_auth_cookie(auth_cookie_path):
    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("Set-Cookie3: auth="):
                    auth_cookie_value = line.split("auth=")[1].split(';')[0].strip()
                    return auth_cookie_value
    return None

# Call the function to choose a friend list backup
selected_file = choose_friendlist_backup()

# Read the auth cookie content
auth_cookie = get_auth_cookie(AUTH_COOKIE_PATH)

# Use the selected file for executing friend requests
if selected_file and auth_cookie:
    print(f"Selected file: {selected_file}")
    execute_friend_requests(selected_file, auth_cookie)
else:
    print("No file selected or AuthCookie not found.")
