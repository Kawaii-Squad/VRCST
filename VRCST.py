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
version = "1.1.0"

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
user_info_file = "LocalDB/temps/User_Info.bin"
user_agent = 'VRCST / Kawaii Squad Studio'
auth_cookie_path = 'LocalDB/temps/AuthCookie.bin'
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
        return defaultdict(list)  # Retourne un defaultdict vide de listes si le fichier n'existe pas
    try:
        with open(log_path, 'r') as log_file:
            data = json.load(log_file)
            return defaultdict(list, data)  # Charge les données depuis le fichier JSON en un defaultdict
    except json.decoder.JSONDecodeError:
        return defaultdict(list)

def update_log_data(log_path, file_hash, file_id_without_extension, target_path):
    log_data = load_log_data(log_path)
    
    if file_hash not in log_data:
        log_data[file_hash] = [file_id_without_extension]
        try:
            with open(log_path, 'w') as log_file:
                json.dump(dict(log_data), log_file, indent=2)
        except IOError as e:
            print(f"Error writing data to {log_path}: {e}")
        print(f"\033[94mOriginal file logged: {file_id_without_extension}\033[0m")
        return False
    
    if file_id_without_extension == log_data[file_hash][0]:
        print(f"\033[94mOriginal file confirmed: {file_id_without_extension}\033[0m")
        return False
    else:
        if os.path.exists(target_path):
            os.remove(target_path)
            print(f"\033[93mDuplicate file removed: {file_id_without_extension}\033[0m")
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
                print("Authentication cookie saved in AuthCookie.bin")
                break

        except Exception as e:
            print("Error during login:", str(e))
            continue

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
                headers = {"User-Agent": user_agent}
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
    # Fonction pour récupérer les informations à partir de l'API VRChat
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

        try:
            if os.path.exists(data_file_path):
                with open(data_file_path, 'r') as file:
                    existing_data = json.load(file)
        except json.decoder.JSONDecodeError as e:
            print(f"Error decoding existing data from {data_file_path}. Error message: {e}")
            existing_data = {}

        existing_data[id_] = data

        try:
            with open(data_file_path, 'w') as file:
                json.dump(existing_data, file, indent=4)
        except IOError as e:
            print(f"Error writing data to {data_file_path}. Error message: {e}")

        print(f"\033[92mInformation successfully recorded for {id_type} ID {id_} : Public.\033[0m")
        return data

    elif response.status_code == 404:
        print(f"\033[91mInformation failed recorded for {id_type} ID {id_} : Private.\033[0m")
        private_info = {"id": id_, "type": id_type, "status": "private"}
        data_file_path = 'LocalDB/temps/Temp_data.json'
        existing_data = {}

        try:
            if os.path.exists(data_file_path):
                with open(data_file_path, 'r') as file:
                    existing_data = json.load(file)
        except json.decoder.JSONDecodeError as e:
            print(f"Error decoding existing data from {data_file_path}. Error message: {e}")
            existing_data = {}

        existing_data[id_] = private_info

        try:
            with open(data_file_path, 'w') as file:
                json.dump(existing_data, file, indent=4)
        except IOError as e:
            print(f"Error writing data to {data_file_path}. Error message: {e}")

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

def start_the_logger(PATH):
    print("\033[95mLogger Started Network & Locally\033[0m")
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
                                print(f"\033[93mFile Analysis: \033[96m{filepath}\033[0m")
                                print(f"\033[95mBlueprint ID Found: \033[96m{blueprint_id}\033[0m")

                                entity_type = 'VRCA' if blueprint_id.startswith('avtr_') else 'VRCW'
                                log_path = os.path.join("LocalDB", "infos", f"ID_REF_{entity_type.upper()}.json")
                                info_path = os.path.join("LocalDB", "infos", f"INFO_{entity_type.upper()}.json")
                                target_path = os.path.join("LocalDB", entity_type, f"{blueprint_id}.{entity_type.lower()}")

                                info = get_info_id(blueprint_id, entity_type)

                                file_hash = hash_file(filepath)
                                is_duplicate = update_log_data(log_path, file_hash, blueprint_id, target_path)

                                if not os.path.exists(target_path) and not is_duplicate:
                                    shutil.copy(filepath, target_path)
                                    print(f"{datetime.datetime.now()} - \033[92m{entity_type} Added Successfully: {blueprint_id}\033[0m")

                                    if info:
                                        save_json_data(info_path, info)
                                        if "imageUrl" in info:
                                            download_entity_image(blueprint_id, entity_type)

                                elif os.path.exists(target_path):
                                    print(f"{datetime.datetime.now()} - \033[91m{entity_type} Already Exists: {blueprint_id}\033[0m")

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

    print("\033[0m")

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

def save_friends_list(username):
    try:
        url = "https://api.vrchat.cloud/api/1/auth/user/friends"
        headers = {"User-Agent": 'VRCST / Kawaii Squad Studio'}
        auth_cookie_path = 'LocalDB/temps/AuthCookie.bin'
        
        with open(auth_cookie_path, "r") as f:
            auth_cookie = f.read().strip()

        cookies = {"auth": auth_cookie}
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
        print(f"{Fore.RED}\nNasa got Hacked by Kaichi-Sama {Fore.GREEN}for question dm Discord : kaichisama.{Fore.RESET}")
        print(f"{Fore.LIGHTMAGENTA_EX}Join : https://t.me/+uIv0MsARg4oyZTBh{Fore.RESET}")
        print(f"{Fore.LIGHTMAGENTA_EX}Powered by Chat GPT{Fore.RESET}")
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
            start_the_logger(PATH)
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

update_files()
fancy_welcome(version)
login_to_vrchat()
music_thread = threading.Thread(target=play_default_music)
music_thread.start()
main_menu()
