import pygame
import os
import re
import sys
import shutil
import datetime
import time
import logging
import threading
import hashlib
import base64
import json
import subprocess
import requests
from collections import defaultdict
import getpass  # Assurez-vous que getpass est importé
from urllib.request import Request
import traceback
import pyfiglet
import webbrowser as wb
import UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.classes.Object import NodeHelper
import keyboard
import vrchatapi
from vrchatapi.api import authentication_api, avatars_api, worlds_api, AuthenticationApi
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode
from vrchatapi.rest import ApiException
from vrchatapi.api_client import ApiClient
from vrchatapi.configuration import Configuration
from colorama import Fore, Style, init
from plyer import notification
from pythonosc import udp_client
import threading
import ctypes
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.style import Style
from colorama import Fore, Style as ColoramaStyle, init
from http.cookiejar import LWPCookieJar

# Notification Windows
def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name='VRCST',
        app_icon=None,
        timeout=10
    )

# Chemins constants
user_directory = os.path.expanduser("~")
LOGS_PATH = os.path.join(user_directory, "Logs")
PATH = os.path.join(user_directory, "AppData", "LocalLow", "VRChat", "VRChat", "Cache-WindowsPlayer")

# VERSION DU LOGICIEL :
version = "2.0.0"

def get_auth_cookie(auth_cookie_path):
    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("Set-Cookie3: auth="):
                    auth_cookie_value = line.split("auth=")[1].split(';')[0].strip()
                    return auth_cookie_value
    return None

local_script_path = "VRCST.py"
user_agent = 'VRCST / Kawaii Squad Studio'
auth_cookie_path = 'LocalDB/temps/AuthCookie.txt'
friendlist_folder = 'LocalDB/infos'
auth_cookie = get_auth_cookie(auth_cookie_path)
IP_VRCHAT = "127.0.0.1"
PORT_VRCHAT_SEND = 9000
# INTERNAL FUNCTIONS
def create_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {directory}. Error message: {e}")

# Fancy Welcome

def fancy_welcome(version, developers=None):
    if developers is None:
        developers = [
            {'name': 'Kaichi-Sama', 'role': 'Lead Developer'},
            {'name': 'Crystaldust', 'role': 'Developer'},
            {'name': '嫌われ者', 'role': 'Developer'},
            {'name': 'ChatGPT', 'role': 'ALL Developer'}
            
        ]

    # Texte ASCII art en vert
    welcome_text = f"""
[green]     /$$    /$$ /$$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$$$
    | $$   | $$| $$__  $$ /$$__  $$ /$$__  $$|__  $$__/
    | $$   | $$| $$  \\ $$| $$  \\__/| $$  \\__/   | $$
    |  $$ / $$/| $$$$$$$/| $$      |  $$$$$$    | $$
     \\  $$ $$/ | $$__  $$| $$       \\____  $$   | $$
      \\  $$$/  | $$  \\ $$| $$    $$ /$$  \\ $$   | $$
       \\  $/   | $$  | $$|  $$$$$$/|  $$$$$$/   | $$
        \\_/    |__/  |__/ \\______/  \\______/    |__/[/green]
    """

    # Texte de remerciement en jaune avec rich
    thank_you_text = Text("Thank you for using the Kawaii VRC Scanner Tool", style="yellow")

    # Box de version
    version_box = f"""
    ╭─── Version ────╮
    │ Version: {version} │
    ╰────────────────╯
    """

    # Tableau des développeurs avec rich
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="bold red")
    table.add_column("Role", style="bold green")

    for dev in developers:
        table.add_row(dev['name'], dev['role'])

    # Affichage avec rich
    console = Console()
    console.print(welcome_text)
    console.print(thank_you_text)
    console.print(version_box)
    console.print(table)

# The File Updater
def update_files():
    files_to_update = {
        "VRCST.py": "https://raw.githubusercontent.com/Kawaii-Squad/VRCST/main/VRCST.py",
        "RunMe.bat": "https://raw.githubusercontent.com/Kawaii-Squad/VRCST/main/RunMe.bat",
        "requirements.txt": "https://raw.githubusercontent.com/Kawaii-Squad/VRCST/main/requirements.txt",
        "README.md": "https://raw.githubusercontent.com/Kawaii-Squad/VRCST/main/README.md"
    }

    for file_name, remote_url in files_to_update.items():
        response = requests.get(remote_url)
        if response.status_code == 200:
            remote_content = response.text.strip()

            try:
                with open(file_name, "r", encoding="utf-8") as local_file:
                    local_content = local_file.read().strip()
            except FileNotFoundError:
                local_content = None

            if local_content != remote_content:
                print(f"Updating {file_name}...")
                with open(file_name, "w", encoding="utf-8") as local_file:
                    local_file.write(remote_content)
                print(f"{file_name} updated successfully.")
            else:
                print(f"{file_name} is already up-to-date.")
        else:
            print(f"Failed to download file {file_name} from {remote_url}. Status code: {response.status_code}")

    # After updating files, restart the script using RunMe.bat
    restart_script()

def restart_script():
    print("Restarting the script...")
    try:
        subprocess.run(["RunMe.bat"], shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while restarting the script: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while restarting the script: {e}")
        
# Login Script

def save_auth_cookie(api_client, filename):
    cookie_jar = LWPCookieJar(filename=filename)
    for cookie in api_client.rest_client.cookie_jar:
        cookie_jar.set_cookie(cookie)
    cookie_jar.save()

def load_auth_cookie(api_client, filename):
    cookie_jar = LWPCookieJar(filename=filename)
    if os.path.exists(filename):
        try:
            cookie_jar.load()
        except Exception as e:
            print(f"Error loading cookies from {filename}: {e}")
            cookie_jar.save()
    else:
        cookie_jar.save()
    for cookie in cookie_jar:
        api_client.rest_client.cookie_jar.set_cookie(cookie)

def login_to_vrchat():
    print("Welcome to the VRChat login script!")

    if os.path.exists(auth_cookie_path):
        configuration = Configuration()
        with ApiClient(configuration) as api_client:
            api_client.user_agent = user_agent
            load_auth_cookie(api_client, auth_cookie_path)

            auth_api = authentication_api.AuthenticationApi(api_client)

            try:
                current_user = auth_api.get_current_user()
                print("\033[92mLogged in as:", current_user.display_name + "\033[0m")
                return  # If authentication is successful, exit the function
            except ApiException as e:
                if "Invalid Username/Email or Password" in str(e):
                    print("Invalid Username/Email or Password. Please try again.")
                else:
                    print("Authentication failed with existing cookie. Login required.")

    while True:
        try:
            username = input("Enter your VRChat username: ")
            password = getpass.getpass("Enter your VRChat password: ")

            configuration = Configuration(
                username=username,
                password=password,
            )

            with ApiClient(configuration) as api_client:
                api_client.user_agent = user_agent
                auth_api = authentication_api.AuthenticationApi(api_client)

                try:
                    current_user = auth_api.get_current_user()
                except ApiException as e:
                    if "Invalid Username/Email or Password" in str(e):
                        print("Invalid Username/Email or Password. Please try again.")
                        continue
                    elif e.status == 200:
                        if "Email 2 Factor Authentication" in e.reason:
                            auth_api.verify2_fa_email_code(two_factor_email_code=TwoFactorEmailCode(input("Email 2FA Code: ")))
                        elif "2 Factor Authentication" in e.reason:
                            two_factor_code = input("2FA Code: ")
                            if two_factor_code:
                                auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(two_factor_code))
                            else:
                                print("Two-Factor Authentication is required, but no code provided.")
                                continue
                        current_user = auth_api.get_current_user()
                    else:
                        print("Exception when calling API:", e)
                        continue

                print("\033[92mLogged in as:", current_user.display_name + "\033[0m")

                # Save the authentication cookie
                save_auth_cookie(api_client, auth_cookie_path)
                print("Authentication cookie saved in AuthCookie.txt")
                break

        except Exception as e:
            print("Error during login:", str(e))
            continue

# LOGGER

def launch_loggerscript():
    try:
        # Specify the exact path to loggerscript.py in the Dependencies/subscripts folder
        loggerscript_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Dependencies", "subscripts", "loggerscript.py")

        # Check if loggerscript.py exists
        if os.path.isfile(loggerscript_path):
            # Use subprocess.Popen to open the script in a new terminal or command prompt window
            if os.name == 'nt':  # Check if the operating system is Windows
                subprocess.Popen(['start', 'cmd', '/k', 'python', loggerscript_path], shell=True)
            else:
                # For Unix-like systems (Linux, macOS), open in a new terminal
                subprocess.Popen(['gnome-terminal', '--', 'python', loggerscript_path], stderr=subprocess.PIPE)

            print(f"Launching {loggerscript_path} for log processing.")
        else:
            print(f"The specified file is not found: {loggerscript_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# LOCAL DATABASE (NOT FINISH)
def research_id_in_local_database(search_id):
    current_directory = os.path.dirname(os.path.realpath(__file__))
    logs_path = os.path.join(current_directory, "Logs")
    file_names = ["ID_REF_VRCA.json", "ID_REF_VRCW.json"]
    file_found = False
    
    for file_name in file_names:
        file_path = os.path.join(logs_path, file_name)
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            for key, id_list in data.items():
                if search_id in id_list:
                    associated_id = id_list[0]
                    file_type = "VRCA" if file_name.endswith("VRCA.json") else "VRCW"
                    associated_file_path = os.path.join(current_directory, file_type, f"{associated_id}.{file_type.lower()}")
                    print(Fore.GREEN + f"The searched ID is associated with: {associated_id}")
                    print(Fore.BLUE + "Here is the direct link to the file:")
                    print(Fore.YELLOW + associated_file_path)
                    file_found = True
                    break
        except FileNotFoundError:
            print(Fore.RED + f"File not found: {file_path}")
        except json.JSONDecodeError:
            print(Fore.RED + f"Could not parse JSON from file: {file_path}")

        if file_found:
            break

    if not file_found:
        print(Fore.RED + "ID not found in any of the provided JSON files.")


# NETWORK DATABASE

def get_display_name():
    if not os.path.exists(auth_cookie_path):
        raise FileNotFoundError(f"Auth cookie path does not exist: {auth_cookie_path}")

    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api_client.user_agent = user_agent
        load_auth_cookie(api_client, auth_cookie_path)

        auth_api = authentication_api.AuthenticationApi(api_client)

        try:
            current_user = auth_api.get_current_user()
            return current_user.display_name
        except ApiException as e:
            raise RuntimeError("Failed to retrieve display name. Check authentication.") from e

def save_friends_list():
    try:
        username = get_display_name()  # Function to retrieve display name
        url = "https://api.vrchat.cloud/api/1/auth/user/friends"
        headers = {"User-Agent": user_agent}
        cookies = {"auth": auth_cookie}

        # Make the request to get friends list
        response = requests.get(url, headers=headers, cookies=cookies)

        if response.status_code == 200:
            friends_list = response.json()
            
            if friends_list:
                friendlist_filename = f'friendlist_{username}.json'
                os.makedirs('LocalDB/infos', exist_ok=True)
                
                with open(f'LocalDB/infos/{friendlist_filename}', 'w', encoding='utf-8') as f:
                    json.dump(friends_list, f, ensure_ascii=False, indent=4)
                    
                print(f"\033[92mFriend list {friendlist_filename} has been updated.\033[0m")
            else:
                print("Empty friends list received.")
        else:
            print(f"Failed to retrieve friends list: {response.status_code}")

    except Exception as e:
        print(f"An error occurred in save_friends_list function: {e}")
        traceback.print_exc()

def launch_friendlistrecovery():
    try:
        # Specify the exact path to friendlistsaver.py (renamed as friendlistrecovery.py)
        friendlistrecovery_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Dependencies", "subscripts", "friendlistsaver.py")

        # Check if friendlistrecovery.py exists
        if os.path.isfile(friendlistrecovery_path):
            # Use subprocess.Popen to open the script in a separate command prompt window on Windows
            if os.name == 'nt':  # Check if operating system is Windows
                subprocess.Popen(['start', 'cmd', '/k', 'python', friendlistrecovery_path], shell=True)
            else:
                # For Unix-like systems (Linux, macOS), open in a separate terminal
                subprocess.Popen(['x-terminal-emulator', '-e', 'python', friendlistrecovery_path])

            print(f"Launching {friendlistrecovery_path} for friend list recovery.")
        else:
            print(f"The specified file is not found: {friendlistrecovery_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Add Network_database_menu function
def Network_database_menu():
    print("Network Database is not finished and needs another developer to fix it. Thanks <3")

# GUI
init()
def main_menu():
    while True:
        print(f"{Fore.RED}\nVRChat got Hacked by Kaichi-Sama {Fore.GREEN}for question dm telegram : .{Fore.RESET}")
        print(f"{Fore.LIGHTMAGENTA_EX}Join : https://t.me/+uIv0MsARg4oyZTBh{Fore.RESET}")
        print(f"{Fore.LIGHTMAGENTA_EX}Powered by Chat GPT{Fore.RESET}")
        print(f"\n{Fore.GREEN}? Kaichi-Sama Menu UwU ?{Fore.RESET}:")
        print("1. Web Management Database")
        print(f"2. Network Database {Fore.RED}Not Finished Need an other Dev for do it Thanks <3{Fore.RESET}")
        print("3. Start The Logger")
        print(f"{Fore.RED}4. DON'T CLICK HERE{Fore.RESET}")
        print("5. Exit/AltF4")
        print("6. Automatic Friendlist request")
        choice = input("Choose an option: ")

        if choice == "1":
            print(f"{Fore.RED}Fuck you i need someone for HTML Local XD{Fore.RESET}")
        elif choice == "2":
            Network_database_menu()
        elif choice == "3":
            launch_loggerscript()
        elif choice == "4":
            print("you get Rickrolled by KawaiiTools Dev Team <3")
            rickroll()
        elif choice == "5":
            print("\nHave Sex with Me!")
            break
        elif choice == "6":
            launch_friendlistrecovery()
        else:
            print("Invalid option, please try again.")

#def local_database_menu():

def rickroll():
    url = 'https://theannoyingsite.com/'
    wb.open(url)

def play_default_music():
    try:
        # Initialisation de pygame
        pygame.init()
        
        # Chemin relatif vers le fichier audio par défaut
        script_directory = os.path.dirname(__file__)
        default_music_path = os.path.join(script_directory, 'Dependencies', '20  Discover the Abyss.mp3')
        
        # Vérification si le fichier existe
        if not os.path.exists(default_music_path):   
            return
        
        # Initialisation du lecteur audio
        pygame.mixer.init()
        
        # Chargement du fichier audio
        pygame.mixer.music.load(default_music_path)
        
        # Lecture de la musique une fois (0 indique une lecture une seule fois)
        pygame.mixer.music.play(loops=0)
        
        # Attente jusqu'à ce que la musique se termine
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Attente pour réduire l'utilisation du processeur
        
    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        print("\nMusic playback stopped.")
    except Exception as e:
        print(f"Error during music playback: {e}")
    finally:
        pygame.quit()

#update_files()
fancy_welcome(version)
login_to_vrchat()
music_thread = threading.Thread(target=play_default_music)
music_thread.start()
save_friends_list()
main_menu()
