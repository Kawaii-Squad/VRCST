# -*- coding: utf-8 -*-
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
from getpass import getpass
from collections import defaultdict
from urllib.request import Request
import traceback
import pyfiglet
import webbrowser as wb
import UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.classes.Object import NodeHelper
import keyboard
import vrchatapi
from vrchatapi.api import authentication_api, avatars_api, worlds_api
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
version = "1.1.0"

# AuthCookie
def get_auth_cookie(auth_cookie_path):
    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, 'r') as file:
            cookie_content = file.read().strip()
            auth_cookie = next((part.split('=')[1] for part in cookie_content.split('; ') if part.startswith('auth=')), None)
            if auth_cookie:
                return auth_cookie
            else:
                return None
    else:
        return None

# Username Saver
def get_display_name():
    if not os.path.exists(user_id_file):
        print(f"User ID file not found: {user_id_file}")
        return None

    with open(user_id_file, 'r') as file:
        user_id = file.read().strip()

    url = f"https://api.vrchat.cloud/api/1/users/{user_id}"
    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    response = requests.get(url, headers=headers, cookies=cookies)

    if response.status_code == 200:
        user_info = response.json()

        if isinstance(user_info, list) and user_info:
            return user_info[0].get('displayName')
        elif isinstance(user_info, dict):
            return user_info.get('displayName')
        else:
            print("Unexpected response format:", user_info)
            return None
    else:
        print(f"Error retrieving user information: {response.status_code}")
        return None

local_script_path = "VRCST.py"
user_id_file = 'LocalDB/temps/user_id.bin'
user_agent = 'VRCST / Kawaii Squad Studio'
auth_cookie_path = 'LocalDB/temps/AuthCookie.bin'
friendlist_folder = 'LocalDB/infos'
auth_cookie = get_auth_cookie(auth_cookie_path)
displayName = get_display_name()
IP_VRCHAT = "127.0.0.1"
PORT_VRCHAT_SEND = 9000

# INTERNAL FUNCTIONS
def create_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {directory}. Error message: {e}")

def extract_blueprint_ids(asset_path):
    env = UnityPy.load(asset_path)
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour':
            data = obj.read()
            if hasattr(data, 'blueprintId') and hasattr(data, 'contentType'):
                return data.blueprintId

def hash_file(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_log_data(log_path):
    if not os.path.exists(log_path):
        return defaultdict(list)
    with open(log_path, 'r') as log_file:
        try:
            data = json.load(log_file)
            return defaultdict(list, data)
        except json.JSONDecodeError:
            return defaultdict(list)

def update_log_data(log_path, file_hash, file_id_without_extension, target_path):
    log_data = load_log_data(log_path)
    if file_hash not in log_data:
        log_data[file_hash] = [file_id_without_extension]
        with open(log_path, 'w') as log_file:
            json.dump(dict(log_data), log_file, indent=2)
        print(f"{Fore.BLUE}Original file logged: {file_id_without_extension}{Style.RESET_ALL}")
        return False
    if file_id_without_extension == log_data[file_hash][0]:
        print(f"{Fore.BLUE}Original file confirmed: {file_id_without_extension}{Style.RESET_ALL}")
        return False
    else:
        if os.path.exists(target_path):
            os.remove(target_path)
            print(f"{Fore.YELLOW}Duplicate file removed: {file_id_without_extension}{Style.RESET_ALL}")
        return True

def run_as_admin(script_path):
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)
        sys.exit()
    else:
        print("The script is already running with administrator privileges.")

# Fancy Welcome

def fancy_welcome(version, developers=None):
    if developers is None:
        developers = [
            {'name': 'Kaichi-Sama', 'role': 'Lead Developer'},
            {'name': 'Crystaldust', 'role': 'Developer'},
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

# Login Script
def login_and_save_auth_cookie():
    print("Welcome to the VRChat login script!")

    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, "r") as f:
            content = f.read()
            auth_cookie = None
            two_factor_auth = None
            for line in content.split(';'):
                if line.startswith('auth='):
                    auth_cookie = line[len('auth='):]
                elif line.startswith('twoFactorAuth='):
                    two_factor_auth = line[len('twoFactorAuth='):]

            if auth_cookie and not two_factor_auth:
                try:
                    response = validate_auth_cookie(auth_cookie)
                    if response.status_code == 200:
                        print("\033[92mLogged in with existing authCookie.\033[0m")
                        save_vrchat_user_id()
                        print("\033[92mLogged as:", displayName, "\033[0m")
                        return
                except Exception as e:
                    print(f"Error validating existing authCookie: {e}")

    perform_login()

def validate_auth_cookie(auth_cookie, current_user=None):
    url = "https://api.vrchat.cloud/api/1/auth"
    headers = {
        "Cookie": f"amplitude_id_a750df50d11f21f712262cbd4c0bab37vrchat.com=string; auth={auth_cookie}",
        "User-Agent": user_agent
    }

    print(f"Sending test request to {url} with headers: {headers}")
    response = requests.get(url, headers=headers)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    return response

def perform_login():
    username = input("Enter your VRChat username: ")
    password = getpass("Enter your VRChat password: ")

    configuration = vrchatapi.Configuration(
        username=username,
        password=password,
    )

    with vrchatapi.ApiClient(configuration) as api_client:
        api_client.user_agent = user_agent
        auth_api = authentication_api.AuthenticationApi(api_client)

        try:
            current_user = auth_api.get_current_user()
            print("Logged in as:", current_user.display_name)
        except UnauthorizedException as e:
            if e.status == 200:
                if "Email 2 Factor Authentication" in e.reason:
                    auth_api.verify2_fa_email_code(two_factor_email_code=TwoFactorEmailCode(input("Email 2FA Code: ")))
                elif "2 Factor Authentication" in e.reason:
                    auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(input("2FA Code: ")))
                current_user = auth_api.get_current_user()
                print("Logged in as:", current_user.display_name)
            else:
                print("Exception when calling API:", e)
        except vrchatapi.ApiException as e:
            print("Exception when calling API:", e)
            return

        print("\033[92mLogged in as:", current_user.display_name + "\033[0m")
        show_notification('Connected Successfully', 'User has successfully logged in.')
        cookies = api_client.rest_client.cookie_jar
        mock_request_object = Request(url="https://api.vrchat.cloud/api/1/auth/user", method="GET")
        cookies.add_cookie_header(mock_request_object)
        auth_cookie = mock_request_object.get_header("Cookie")

        os.makedirs("LocalDB/temps", exist_ok=True)

        with open(auth_cookie_path, "wb") as f:
            f.write(auth_cookie.encode())
        print("Authentication cookie saved in AuthCookie.bin")

        save_vrchat_user_id()

# Restart Fonction
def restart_program():
    print("\033[92mRestarting program... Please wait.\033[0m")
    python = sys.executable
    os.execl(python, python, *sys.argv)

# UserID Saver
def save_vrchat_user_id():
    url = "https://api.vrchat.cloud/api/1/auth/user"
    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        user_info = response.json()
        user_id = user_info.get('id')

        with open(user_id_file, 'wb') as file:
            file.write(user_id.encode('utf-8'))

        print("User ID successfully saved in the logs directory.")
        return True
    else:
        print(f"Error retrieving user information: {response.status_code}")
        print("\033[92mRestarting program... Please wait.\033[0m")
        restart_program()  # Redémarre le programme en cas d'échec
        return False

# LOGGER
def download_entity_image(entity_id, entity_type):
    logging.basicConfig(filename='LocalDB/temps/download_log.log', level=logging.INFO, format='%(asctime)s %(message)s')

    file_path = f'LocalDB/infos/INFO_{entity_type}.json'

    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found.")
        return

    with open(file_path, 'r') as file:
        try:
            entities_info = json.load(file)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to load JSON from {file_path}: {e}")
            return

    for entity_info in entities_info:
        if 'id' in entity_info and entity_info['id'] == entity_id:
            image_url = entity_info.get('imageUrl')
            if not image_url:
                logging.warning(f"No image URL for entity ID {entity_id}")
                return

            try:
                headers = {'User-Agent': 'VRC Scanner Tool / Kawaii Squad'}
                response = requests.get(image_url, headers=headers)
                response.raise_for_status()

                image_filename = f"{entity_id}.png"
                image_folder = os.path.join('LocalDB', 'images', 'AvatarsPNG' if entity_type == 'VRCA' else 'WorldsPNG')
                os.makedirs(image_folder, exist_ok=True)
                image_path = os.path.join(image_folder, image_filename)

                with open(image_path, 'wb') as image_file:
                    image_file.write(response.content)

                logging.info(f"Image uploaded successfully for entity ID {entity_id}")
                return
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to upload image for entity ID {entity_id}: {e}")
                return

    logging.warning(f"Entity ID {entity_id} was not found in {file_path}")

def get_info_id(id_, id_type):
    url = f"https://api.vrchat.cloud/api/1/{'avatars' if id_type == 'VRCA' else 'worlds'}/{id_}" if id_type in ['VRCA', 'VRCW'] else None

    if not url:
        print(f"Unsupported ID type: {id_type}")
        return None

    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            print(f"Error decoding JSON response for {id_type} ID {id_}. Response content: {response.text}")
            return None

        data_file_path = 'LocalDB/temps/Temp_data.json'
        existing_data = {}

        if os.path.exists(data_file_path):
            try:
                with open(data_file_path, 'r') as file:
                    existing_data = json.load(file)
            except json.decoder.JSONDecodeError:
                print(f"Error decoding existing data from {data_file_path}. File content: {file.read()}")
                existing_data = {}

        existing_data[id_] = data

        with open(data_file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)

        print(f"\033[92mInformations successfully recorded for {id_type} ID {id_} : Public.\033[0m")
        return data
    elif response.status_code == 404:
        print(f"\033[91mInformations failed recorded for {id_type} ID {id_} : Private.\033[0m")
        private_info = {"id": id_, "type": id_type, "status": "private"}
        data_file_path = 'LocalDB/temps/Temp_data.json'
        existing_data = {}

        if os.path.exists(data_file_path):
            try:
                with open(data_file_path, 'r') as file:
                    existing_data = json.load(file)
            except json.decoder.JSONDecodeError:
                print(f"Error decoding existing data from {data_file_path}. File content: {file.read()}")
                existing_data = {}

        existing_data[id_] = private_info

        with open(data_file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)

        save_json_data(f'LocalDB/infos/INFO_{id_type}.json', private_info)
        return private_info
    else:
        print(f"\033[91mUnexpected response status: {response.status_code} for {id_type} ID {id_}.\033[0m")
        return None

def save_json_data(file_path, new_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            existing_data = []
    else:
        existing_data = []

    existing_ids = {data['id'] for data in existing_data if 'id' in data}
    if 'id' in new_data and new_data['id'] in existing_ids:
        for i, data in enumerate(existing_data):
            if data['id'] == new_data['id']:
                existing_data[i] = new_data
                break
    else:
        existing_data.append(new_data)

    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=2)

def start_the_logger():
    print(f"{Fore.LIGHTMAGENTA_EX}Logger Started Network & Locally{Style.RESET_ALL}")
    create_directory("LocalDB/VRCA")
    create_directory("LocalDB/VRCW")
    create_directory("LocalDB/infos")

    log_vrca_path = os.path.join("LocalDB", "infos", "ID_REF_VRCA.json")
    log_vrcw_path = os.path.join("LocalDB", "infos", "ID_REF_VRCW.json")

    processed_dirs = set()
    last_processed_time = None

    while True:
        new_processed_dirs = set()
        has_processed_files = False

        for root, dirs, files in os.walk(PATH):
            if root not in processed_dirs or last_processed_time is None or os.path.getmtime(root) > last_processed_time:
                new_processed_dirs.add(root)
                files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(root, x)))
                for file in files:
                    if file.endswith('__data'):
                        filepath = os.path.join(root, file)
                        try:
                            blueprint_id = extract_blueprint_ids(filepath)
                            if blueprint_id:
                                print(f"{Fore.YELLOW}File Analysis: {Fore.LIGHTCYAN_EX}{filepath}{Style.RESET_ALL}", end="")
                                print(f"\n{Fore.MAGENTA}Blueprint ID Found: {Fore.LIGHTCYAN_EX}{blueprint_id}{Style.RESET_ALL}")

                                entity_type = 'VRCA' if blueprint_id.startswith('avtr_') else 'VRCW'
                                log_path = os.path.join("LocalDB", "infos", f"ID_REF_{entity_type.upper()}.json")
                                info_path = os.path.join("LocalDB", "infos", f"INFO_{entity_type.upper()}.json")
                                target_path = os.path.join("LocalDB", entity_type, f"{blueprint_id}.{entity_type.lower()}")

                                info = get_info_id(blueprint_id, entity_type)

                                file_hash = hash_file(filepath)
                                is_duplicate = update_log_data(log_path, file_hash, blueprint_id, target_path)

                                if not os.path.exists(target_path) and not is_duplicate:
                                    shutil.copy(filepath, target_path)
                                    print(f"{datetime.datetime.now()} - {Fore.GREEN}{entity_type} Added Successfully: {blueprint_id}{Style.RESET_ALL}")

                                    if info:
                                        save_json_data(info_path, info)
                                        if "imageUrl" in info:
                                            download_entity_image(blueprint_id, entity_type)

                                elif os.path.exists(target_path):
                                    print(f"{datetime.datetime.now()} - {Fore.RED}{entity_type} Already Exists: {blueprint_id}{Style.RESET_ALL}")

                                has_processed_files = True
                                print()

                        except Exception as e:
                            print(f"Error reading file {filepath}. Error message: {e}")
                            import traceback
                            traceback.print_exc()

        if not has_processed_files:
            print(f"{datetime.datetime.now()} - Waiting for new files...")
            time.sleep(60)

        processed_dirs.update(new_processed_dirs)
        last_processed_time = time.time()

    print(Style.RESET_ALL)

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

def display_all_ids_in_cache():
    print("\nDisplaying All IDs in Your Cache:")
    for root, dirs, files in os.walk(PATH):
        for file in files:
            if file.endswith('__data'):
                filepath = os.path.join(root, file)
                try:
                    blueprint_id = extract_blueprint_ids(filepath)
                    if blueprint_id:
                        id_type = "Avatar" if blueprint_id.startswith('avtr_') else "World"
                        id_color = Fore.LIGHTYELLOW_EX if id_type == "Avatar" else Fore.LIGHTMAGENTA_EX
                        print(f"{Fore.YELLOW}File Analysis: {Fore.LIGHTCYAN_EX}{filepath}{Fore.RESET}")
                        print(f"{datetime.datetime.now()} - {id_color}{id_type} ID : {Fore.GREEN}{blueprint_id}{Fore.RESET}")
                except Exception as e:
                    print(f"Error reading file {filepath}. Error message: {e}")

def display_ids_filtered(option):
    if option == "World":
        folder = "LocalDB/VRCW"
        entity = "World"
    elif option == "Avatar":
        folder = "LocalDB/VRCA"
        entity = "Avatar"
    else:
        print("Invalid option, please try again.")
        return

    print(f"\n\033[33mDisplaying {entity} Info in Local Database:\033[0m")
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(f".{folder.lower()}"):
                entity_id = os.path.splitext(file)[0]
                print(f"\033[92m{entity} ID: \033[95m{entity_id}\033[0m")

# NETWORK DATABASE

def save_friends_list(displayName):
    try:
        auth_cookie = get_auth_cookie(auth_cookie_path)
        if not auth_cookie:
            print("No valid auth cookie found. Exiting function.")
            return

        url = "https://api.vrchat.cloud/api/1/auth/user/friends"
        headers = {"User-Agent": user_agent}
        cookies = {"auth": auth_cookie}

        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            friends_list = response.json()
            
            # Vérifie si la liste d'amis n'est pas vide
            if friends_list:
                friendlist_filename = os.path.join(friendlist_folder, f'friendlist_{displayName}.json')
                
                # Assurez-vous que le dossier existe avant d'écrire dans le fichier
                os.makedirs(friendlist_folder, exist_ok=True)
                
                with open(friendlist_filename, 'w', encoding='utf-8') as f:
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
            # Run friendlistrecovery.py using subprocess.Popen
            subprocess.Popen(["python", friendlistrecovery_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        print(f"{Fore.RED}\nNasa got Hacked by Kaichi-Sama {Fore.GREEN}for question dm Discord : kaichisama.{Fore.RESET}")
        print(f"{Fore.LIGHTMAGENTA_EX}Join : https://t.me/+uIv0MsARg4oyZTBh{Fore.RESET}")
        print(f"{Fore.LIGHTMAGENTA_EX}Powered by Kawaii Squad Devs : Kaichi-Sama / >_Unknown User{Fore.RESET}")
        print(f"\n{Fore.GREEN}? Kaichi-Sama Menu UwU ?{Fore.RESET}:")
        print("1. Local Database")
        print(f"2. Network Database {Fore.RED}Not Finished Need an other Dev for fix it Thanks <3{Fore.RESET}")
        print("3. Start The Logger")
        print(f"{Fore.RED}4. DON'T CLICK HERE{Fore.RESET}")
        print("5. Exit")
        print("6. Automatic Friendlist request")
        choice = input("Choose an option: ")

        if choice == "1":
            local_database_menu()
        elif choice == "2":
            Network_database_menu()
        elif choice == "3":
            start_the_logger()
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

def local_database_menu():
    while True:
        print("\nLocal Database Menu:")
        print("1. Display All IDs in Cache")
        print("2. Filtered Local Research")
        print("3. Research an ID in LocalDatabase")
        print("4. Back to Main Menu")

        choice = input("Choose an option: ")

        if choice == "1":
            display_all_ids_in_cache()
        elif choice == "2":
            print("\nSub-Menu:")
            print("1. Display World Info")
            print("2. Display Avatar Info")
            sub_choice = input("Choose an option: ")

            if sub_choice == "1":
                display_ids_filtered("World")
            elif sub_choice == "2":
                display_ids_filtered("Avatar")
            else:
                print("Invalid option, please try again.")
        elif choice == "3":
            search_id = input("\nEnter the ID you want to research in the LocalDatabase: ")
            research_id_in_local_database(search_id)
        elif choice == "4":
            break
        else:
            print("Invalid option, please try again.")

def rickroll():
    url = 'https://www.youtube.com/watch?v=0wpvkIkAkbk&list=RDMM'
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

update_files()
fancy_welcome(version)
login_and_save_auth_cookie()
save_friends_list(displayName)
music_thread = threading.Thread(target=play_default_music)
music_thread.start()
main_menu()
