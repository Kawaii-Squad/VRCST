import os
import re
import sys
import shutil
from colorama import Fore, Style, init
import datetime
import time
import logging
import colorama
import hashlib
import base64
import json
import subprocess
import pkg_resources
import logging
from getpass import getpass
from collections import defaultdict
import requests
from urllib.request import Request
import traceback
import pyfiglet
import webbrowser as wb
import UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.classes.Object import NodeHelper
import keyboard  # Import keyboard module for keypress handling 
import vrchatapi
from vrchatapi.api import authentication_api
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode
from vrchatapi.api import avatars_api, worlds_api
from vrchatapi.rest import ApiException
from vrchatapi.api_client import ApiClient
from vrchatapi.configuration import Configuration
from collections import defaultdict
from colorama import Fore, Style, init
import colorama  # Ajout de l'importation manquante
from plyer import notification
from pythonosc import udp_client
import threading

init(autoreset=True)
user_directory = os.path.expanduser("~")

# Chemins constants
LOGS_PATH = os.path.join(user_directory, "Logs")
PATH = os.path.join(user_directory, "AppData", "LocalLow", "VRChat", "VRChat", "Cache-WindowsPlayer")
#VERSION DU LOGICIEL :
version = "1.1.0"
# Définition du chemin local du script
local_script_path = "VRChatScanner.py"
user_id_file = 'Logs/user_id.bin'  # Nom du fichier pour enregistrer le user ID
user_agent = 'VRC Scanner Tool / Kawaii Squad'
auth_cookie_path = 'Logs/AuthCookie.bin'

# Fonction pour afficher une notification
def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name='LocalAvatarLogger',  # Nom de votre application
        app_icon=None,  # Chemin vers l'icône de l'application (si nécessaire)
        timeout=10  # Durée en secondes pendant laquelle la notification est affichée
    )

# Ajoutez un argument de ligne de commande pour contrôler la vérification des mises à jour
check_updates_flag = "--check-updates"

def download_file(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.replace('\r\n', '\n').strip()
    else:
        print(f"Failed to download file from {url}. Status code: {response.status_code}")
        return None

def update_file(local_path, remote_url):
    latest_content = download_file(remote_url)
    update_made = False

    if latest_content is not None:
        try:
            with open(local_path, "r", encoding="utf-8") as local_file:
                local_content = local_file.read().replace('\r\n', '\n').strip()
        except FileNotFoundError:
            local_content = None

        if local_content != latest_content:
            print(f"Updating {local_path}...")
            with open(local_path, "w", encoding="utf-8") as local_file:
                local_file.write(latest_content)
            update_made = True
            print(f"{local_path} updated successfully.")
        else:
            print(f"{local_path} is already up-to-date.")
    else:
        print(f"Unable to check for updates for {local_path}. Please try again later.")
    
    return update_made

files_to_update = {
    "VRChatScanner.py": "https://raw.githubusercontent.com/KaichiSama/VRCScannerTool/main/VRChatScanner.py",
    "RunMe.bat": "https://raw.githubusercontent.com/KaichiSama/VRCScannerTool/main/RunMe.bat",
    "requirements.txt": "https://raw.githubusercontent.com/KaichiSama/VRCScannerTool/main/requirements.txt",
    "README.md": "https://raw.githubusercontent.com/KaichiSama/VRCScannerTool/main/README.md"
}

def check_for_updates(force_check=False):
    updates_made = False
    if force_check:
        for local_path, remote_url in files_to_update.items():
            if update_file(local_path, remote_url):
                updates_made = True
    return updates_made

# Vérifiez si l'argument --check-updates est présent
force_check_updates = check_updates_flag in sys.argv

# Si l'argument est présent ou si c'est le premier lancement, vérifiez les mises à jour
if force_check_updates or len(sys.argv) == 1:
    updates_made = check_for_updates(force_check=True)

    if updates_made:
        print("Updates were made. Restarting the script...")
        os.execv(sys.executable, ['python'] + sys.argv[:1] + [check_updates_flag])
    else:
        print("No updates were made. Continuing normal operation.")
else:
    print("Skipping update check on restart. Continuing with the rest of the script.")
# Configuration VRChat
IP_VRCHAT = "127.0.0.1"  # Adresse IP de votre instance VRChat
PORT_VRCHAT_SEND = 9000  # Port d'envoi OSC de VRChat

def send_osc_message(address, *args):
    client = udp_client.SimpleUDPClient(IP_VRCHAT, PORT_VRCHAT_SEND)
    client.send_message(address, args)

# "Kawaii Gang Avatar Reaper Free"
def advertise_kawaii_gang():
    kawaii_frames = [
        "🌈 Thanks for use Kawaii Squad Script 🌸",
        "🌟 Discover amazing assets with us! ✨",
        "🎉 Visit our community for free leaks! 🎊",
        "🌈 Join Kawaii Squad Free! 🌸"
    ]

    # Adresse OSC pour envoyer un message au chatbox de VRChat
    chatbox_address = "/chatbox/input"

    for frame in kawaii_frames:
        send_osc_message(chatbox_address, frame)
        time.sleep(2)

# Fancy Welcome
def fancy_welcome(version, developers=None):
    if developers is None:
        developers = [
            {'name': 'Kaichi-Sama', 'role': 'Lead Developer'},
            {'name': 'Freakiv3', 'role': 'Backend Developer'},  # Ajout de Freakiv3 en tant que Backend Developer
        ]
    
    # ANSI escape codes for colors
    pink_color = '\033[95m'
    green_color = '\033[92m'
    red_color = '\033[91m'
    light_cyan_color = '\033[96m'
    violet_color = '\033[95m'  # Nouvelle couleur violette
    reset_color = '\033[0m'
    box_width = 78  # The total width of the box

    # ASCII Art text for "Welcome to Kawaii Squad"
    welcome_text = r"""

 /$$$$$$$                                                 /$$$$$$  /$$ /$$                       /$$    
| $$__  $$                                               /$$__  $$| $$|__/                      | $$    
| $$  \ $$  /$$$$$$  /$$    /$$ /$$$$$$  /$$$$$$$       | $$  \__/| $$ /$$  /$$$$$$  /$$$$$$$  /$$$$$$  
| $$$$$$$/ |____  $$|  $$  /$$//$$__  $$| $$__  $$      | $$      | $$| $$ /$$__  $$| $$__  $$|_  $$_/  
| $$__  $$  /$$$$$$$ \  $$/$$/| $$$$$$$$| $$  \ $$      | $$      | $$| $$| $$$$$$$$| $$  \ $$  | $$    
| $$  \ $$ /$$__  $$  \  $$$/ | $$_____/| $$  | $$      | $$    $$| $$| $$| $$_____/| $$  | $$  | $$ /$$
| $$  | $$|  $$$$$$$   \  $/  |  $$$$$$$| $$  | $$      |  $$$$$$/| $$| $$|  $$$$$$$| $$  | $$  |  $$$$/
|__/  |__/ \_______/    \_/    \_______/|__/  |__/       \______/ |__/|__/ \_______/|__/  |__/   \___/  
                                                                                                        
                                                                                                        
                                                                                                        
    """

    # Thank you message
    thank_you_text = "Thank you for using the Kawaii VRC Scanner Tool"

    # Version Box
    version_box = f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                    Version: {version:<}                                ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

    # Print the welcome message in pink
    print(pink_color + welcome_text + reset_color)
    # Print the thank you message in light cyan
    print(light_cyan_color + thank_you_text + reset_color)
    # Print the version box
    print(light_cyan_color + version_box + reset_color)

    # Heading for the developers section
    developers_heading = "Developers and Contributors"
    # Start of the box
    print(pink_color + "╔" + "═" * (box_width - 2) + "╗" + reset_color)
    # Heading
    print(pink_color + "║" + developers_heading.center(box_width - 2) + "║" + reset_color)
    # Separator
    print(pink_color + "║" + "─" * (box_width - 2) + "║" + reset_color)
    # List each developer and their role
    for dev in developers:
        name = dev.get('name', 'Unknown')
        role = dev.get('role', 'Contributor')
        # Prepare name and role with color
        name_colored = green_color + name + reset_color
        role_colored = red_color + role + reset_color
        # Creating the entry
        dev_entry = f"{name_colored} - {role_colored}"
        # Calculate the necessary padding
        padding = box_width - 2 - len(name) - len(role) - 3  # 3 for ' - ' between name and role
        left_padding = padding // 2
        right_padding = padding - left_padding
        # Print the entry
        print(pink_color + "║" + " " * left_padding + dev_entry + " " * right_padding + "║" + reset_color)
    # End of the box
    print(pink_color + "╚" + "═" * (box_width - 2) + "╝" + reset_color)
fancy_welcome(version)

# VRCHAT API
show_notification('Kawaii Squad', 'The LocalAvatarLogger script was launched successfully.')
advertise_kawaii_gang()
#HERE PUT AUTH CODE
def login_and_save_auth_cookie():
    print("Welcome to the VRChat login script!")

    # Check if AuthCookie file exists and is valid
    if os.path.exists("logs/AuthCookie.bin"):
        with open("logs/AuthCookie.bin", "r") as f:
            auth_cookie = f.read()

        configuration = vrchatapi.Configuration()
        configuration.api_key['cookie'] = auth_cookie

        try:
            with vrchatapi.ApiClient(configuration) as api_client:
                auth_api = vrchatapi.AuthenticationApi(api_client)
                current_user = auth_api.get_current_user()
                print("\033[92mLogged in as:", current_user.display_name + "\033[0m")
                
                return  # If authentication is successful, exit the function
        except vrchatapi.ApiException as e:
            if "Invalid Username/Email or Password" in str(e):
                print("Invalid Username/Email or Password. Please try again.")
                wait_and_restart()
            else:
                print("Authentication failed with existing cookie. Login required.")

    try:
        # Prompt the user for their username and password
        username = input("Enter your VRChat username: ")
        password = getpass("Enter your VRChat password: ")

        configuration = vrchatapi.Configuration(
            username=username,
            password=password,
        )

        with vrchatapi.ApiClient(configuration) as api_client:
            auth_api = vrchatapi.AuthenticationApi(api_client)

            try:
                current_user = auth_api.get_current_user()
            except vrchatapi.ApiException as e:
                if "Invalid Username/Email or Password" in str(e):
                    print("Invalid Username/Email or Password. Please try again.")
                    wait_and_restart()
                elif e.status == 200:
                    if "Email 2 Factor Authentication" in e.reason:
                        auth_api.verify2_fa_email_code(two_factor_email_code=vrchatapi.TwoFactorEmailCode(input("Email 2FA Code: ")))
                    elif "2 Factor Authentication" in e.reason:
                        two_factor_code = input("2FA Code: ")
                        if two_factor_code:
                            auth_api.verify2_fa(two_factor_auth_code=vrchatapi.TwoFactorAuthCode(two_factor_code))
                        else:
                            print("Two-Factor Authentication is required, but no code provided.")
                            return
                    current_user = auth_api.get_current_user()
                else:
                    print("Exception when calling API:", e)
                    wait_and_restart()

            print("\033[92mLogged in as:", current_user.display_name + "\033[0m")
            show_notification('Connecté avec Succès', 'L\'utilisateur est connecté avec succès.')
            cookies = api_client.rest_client.cookie_jar
            mock_request_object = Request(url="https://api.vrchat.cloud/api/1/auth/user", method="GET")
            cookies.add_cookie_header(mock_request_object)
            auth_cookie = mock_request_object.get_header("Cookie")

            os.makedirs("logs", exist_ok=True)

            with open("logs/AuthCookie.bin", "wb") as f:
                f.write(auth_cookie.encode())
            print("Authentication cookie saved in AuthCookie.bin")

    except Exception as e:
        print("Error during login:", str(e))
        wait_and_restart()

def wait_and_restart():
    show_notification("Identifiants incorrects", "Invalid Username/Email or Password. Please try again.")
    
    print("Waiting for 5 seconds before restarting the script...")
    time.sleep(5)
    
    # Efface la console
    if os.name == 'nt':  # Si le système d'exploitation est Windows
        os.system('cls')
    else:  # Pour d'autres systèmes d'exploitation comme Linux ou macOS
        os.system('clear')
    
    print("Restarting...")
    
    python = sys.executable
    os.execl(python, python, *sys.argv)

def save_vrchat_user_id():
    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, 'r') as file:
            cookie_content = file.read().strip()
            auth_cookie = next((part for part in cookie_content.split('; ') if part.startswith('auth=')), None)
            if not auth_cookie:
                print("Auth cookie value not found in the file.")
                return False
    else:
        print("Auth cookie file not found. Please log in first.")
        return False

    url = "https://api.vrchat.cloud/api/1/auth/user"
    headers = {"User-Agent": user_agent}
    cookies = {auth_cookie.split('=')[0]: auth_cookie.split('=')[1]}

    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        user_info = response.json()
        user_id = user_info.get('id')

        # Save the user ID in the specified file in the Logs directory
        with open(os.path.join(user_id_file), 'wb') as file:
            file.write(user_id.encode('utf-8'))
        print("User ID successfully saved in the logs directory.")
        return True
    else:
        print(f"Error retrieving user information: {response.status_code}")
        return False
    
def create_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {directory}. Error message: {e}")
        
# Ajout de la fonction 'getpass' manquante
def getpass(prompt):
    try:
        import msvcrt
        print(prompt, end='', flush=True)
        password = ""
        while True:
            key = msvcrt.getch()
            if key == b'\r' or key == b'\n':
                print('')
                break
            elif key == b'\x08':
                password = password[:-1]
                print('\b \b', end='', flush=True)
            else:
                password += key.decode()
                print('*', end='', flush=True)
        return password
    except Exception:
        return input(prompt)

#get info Avatars/worlds
def download_entity_image(entity_id, entity_type):
    logging.basicConfig(filename='logs/download_log.log', level=logging.INFO, format='%(asctime)s %(message)s')

    # Construire le chemin du fichier en fonction du type d'entité
    file_name_suffix = "AVATARS" if entity_type == "VRCA" else "WORLDS"
    file_path = f'logs/INFO_{file_name_suffix}.json'

    # Vérifier l'existence du fichier
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found.")
        return

    # Charger les données du fichier
    with open(file_path, 'r') as file:
        entities_info = json.load(file)

    # Rechercher l'entité par ID et télécharger l'image
    for entity_info in entities_info:
        if entity_info.get('id') == entity_id:
            image_url = entity_info.get('imageUrl')
            if not image_url:
                logging.warning(f"No image URL for entity ID {entity_id}")
                return

            try:
                headers = {'User-Agent': 'VRC Scanner Tool / Kawaii Squad'}
                response = requests.get(image_url, headers=headers)
                response.raise_for_status()

                image_filename = f"{entity_id}.png"
                image_folder = os.path.join('logs', 'images', 'AvatarsPNG' if entity_type == 'VRCA' else 'WorldsPNG')
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
    # Charger le cookie d'authentification
    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, 'r') as file:
            cookie_content = file.read().strip()
            # Extraire la valeur du cookie 'auth'
            auth_cookie = next((part.split('=')[1] for part in cookie_content.split('; ') if part.startswith('auth=')), None)
            if not auth_cookie:
                print("Auth cookie value not found in the file.")
                return None
    else:
        print("Auth cookie file not found. Please log in first.")
        return None

    # Définir l'URL de la requête
    url = f"https://api.vrchat.cloud/api/1/{'avatars' if id_type == 'VRCA' else 'worlds'}/{id_}" if id_type in ['VRCA', 'VRCW'] else None

    if not url:
        print(f"Unsupported ID type: {id_type}")
        return None

    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        # Traitement des données et écriture dans Temp_data.json
        data = response.json()
        data_file_path = 'logs/Temp_data.json'
        existing_data = {}
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as file:
                existing_data = json.load(file)
        
        # Ajouter ou mettre à jour les informations de l'ID dans les données existantes
        existing_data[id_] = data

        # Écrire les données mises à jour dans le fichier Temp_data.json
        with open(data_file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
        
        print(f"\033[92mInformations successfully recorded for {id_type} ID {id_} : Public.\033[0m")
        return data
    elif response.status_code == 404:
        print(f"\033[91mInformations failed recorded for {id_type} ID {id_} : Private.\033[0m")
        return None
    else:
        # Si le code de statut n'est ni 200 ni 404, traiter comme une erreur
        print(f"\033[91mUnexpected response status: {response.status_code} for {id_type} ID {id_}.\033[0m")
        return None

def save_json_data(file_path, new_data):
    # Charger les données existantes, sinon initialiser une liste vide
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            existing_data = json.load(file)
    else:
        existing_data = []

    # Vérifier les doublons et les mettre à jour
    existing_ids = {data['id'] for data in existing_data if 'id' in data}
    if 'id' in new_data and new_data['id'] in existing_ids:
        # Mettre à jour l'entrée existante
        for i, data in enumerate(existing_data):
            if data['id'] == new_data['id']:
                existing_data[i] = new_data
                break
    else:
        # Ajouter les nouvelles données
        existing_data.append(new_data)

    # Enregistrer les données mises à jour
    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=2)

#start le logger
def hash_file(filepath):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
  
def load_log_data(log_path):
    """Load existing log data from a JSON file."""
    if not os.path.exists(log_path):
        return defaultdict(list)
    with open(log_path, 'r') as log_file:
        try:
            data = json.load(log_file)
            return defaultdict(list, data)  # Ensure it's a defaultdict
        except json.JSONDecodeError:
            return defaultdict(list)

def update_log_data(log_path, file_hash, file_id_without_extension, target_path):
    """Update log data with a new associated ID under the same HASH_ID."""
    log_data = load_log_data(log_path)

    # Check if the hash already exists in the log data
    if file_hash not in log_data:
        # It's a new file, so log it
        log_data[file_hash] = [file_id_without_extension]
        with open(log_path, 'w') as log_file:
            json.dump(dict(log_data), log_file, indent=2)
        print(f"{Fore.BLUE}Original file logged: {file_id_without_extension}{Style.RESET_ALL}")
        return False

    # If the hash exists, check if it's the same file ID
    if file_id_without_extension == log_data[file_hash][0]:
        # It's the original file
        print(f"{Fore.BLUE}Original file confirmed: {file_id_without_extension}{Style.RESET_ALL}")
        return False  # This is the original file, not a duplicate
    else:
        # It's a different file with the same hash, treat it as a duplicate
        if os.path.exists(target_path):
            os.remove(target_path)
            print(f"{Fore.YELLOW}Duplicate file removed: {file_id_without_extension}{Style.RESET_ALL}")
        return True  # This is a duplicate

def extract_blueprint_ids(asset_path):
    # Chargez le fichier d'asset
    env = UnityPy.load(asset_path)
    # Parcourez tous les objets dans l'environnement du fichier d'asset
    for obj in env.objects:
        # Vérifiez si l'objet est un MonoBehaviour
        if obj.type.name == 'MonoBehaviour':
            # Parsez les données de MonoBehaviour
            data = obj.read()
            # Si data contient une propriété 'blueprintId', affichez-la         
            if hasattr(data, 'blueprintId')and hasattr(data, 'contentType'):
                return data.blueprintId

def start_the_logger():
    print(f"{Fore.LIGHTMAGENTA_EX}Logger Started Network & Locally{Style.RESET_ALL}")
    create_directory("Logs")
    create_directory("VRCA")
    create_directory("VRCW")

    log_vrca_path = os.path.join("Logs", "ID_REF_VRCA.json")
    log_vrcw_path = os.path.join("Logs", "ID_REF_VRCW.json")

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

                                # Déterminez le type d'entité et le chemin de log approprié
                                entity_type = 'VRCA' if blueprint_id.startswith('avtr_') else 'VRCW'
                                log_path = log_vrca_path if entity_type == 'VRCA' else log_vrcw_path
                                info_path = 'logs/INFO_AVATARS.json' if entity_type == 'VRCA' else 'logs/INFO_WORLDS.json'
                                target_path = os.path.join(entity_type, f"{blueprint_id}.{entity_type.lower()}")

                                file_hash = hash_file(filepath)
                                is_duplicate = update_log_data(log_path, file_hash, blueprint_id, target_path)

                                if not os.path.exists(target_path) and not is_duplicate:
                                    shutil.copy(filepath, target_path)
                                    print(f"{datetime.datetime.now()} - {Fore.GREEN}{entity_type} Added Successfully: {blueprint_id}{Style.RESET_ALL}")
                                    
                                    info = get_info_id(blueprint_id, entity_type)
                                    if info:
                                        save_json_data(info_path, info)
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

#affiche tout les ids dans le cache
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
                        print(f"{Fore.YELLOW}File Analysis: {Fore.LIGHTCYAN_EX}{filepath}{Style.RESET_ALL}", end="")
                        print()
                        print(f"{datetime.datetime.now()} - {id_color}{id_type} ID : {Fore.GREEN}{blueprint_id}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"Error reading file {filepath}. Error message: {e}")
#search ID in Cache
def search_in_cache(search_id):
    found_in_cache = False

    for root, dirs, files in os.walk(PATH):
        for file in files:
            if file == '__data':
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding="utf-8", errors='ignore') as f:
                        data = f.read()
                        if search_id in data:
                            print(f"{Fore.YELLOW}File Analysis: {Fore.LIGHTCYAN_EX}{filepath}{Style.RESET_ALL}", end="")
                            print(f"{datetime.datetime.now()} - ID {search_id} found in: {Fore.LIGHTCYAN_EX}{filepath}{Style.RESET_ALL}")
                            found_in_cache = True
                except Exception as e:
                    print(f"Error reading file {filepath}. Error message: {e}")

    if found_in_cache:
        print(f"{Fore.GREEN}Avatar {search_id} found in cache.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Avatar {search_id} not found in cache.{Style.RESET_ALL}")
#Display Filtering
def display_ids_filtered(option):
    if option == "World":
        folder = "VRCW"
        entity = "World"
    elif option == "Avatar":
        folder = "VRCA"
        entity = "Avatar"
    else:
        print("Invalid option, please try again.")
        return

    print(f"\nDisplaying {entity} Info in Local Database:")
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(f".{folder.lower()}"):
                entity_id = os.path.splitext(file)[0]
                print(f"{entity} ID: {entity_id}")

# Initialise Colorama
colorama.init(autoreset=True)

def display_world_info():
    print("\033[33mDisplaying World Info in Local Database:\033[0m")
    for root, dirs, files in os.walk("VRCW"):
        for file in files:
            if file.endswith(".vrcw"):
                world_id = os.path.splitext(file)[0]
                print(f"\033[95mWorld ID: \033[92m{world_id}\033[0m")

def display_avatar_info():
    print("\033[33mDisplaying Avatar Info in Local Database:\033[0m")
    for root, dirs, files in os.walk("VRCA"):
        for file in files:
            if file.endswith(".vrca"):
                avatar_id = os.path.splitext(file)[0]
                print(f"\033[93mAvatar ID: \033[92m{avatar_id}\033[0m")

#research id in local database   
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
                    associated_id = id_list[0]  # Take the first ID in the list
                    # Determine whether the associated ID is VRCA or VRCW
                    file_type = "VRCA" if file_name.endswith("VRCA.json") else "VRCW"
                    associated_file_path = os.path.join(current_directory, file_type, f"{associated_id}.{file_type.lower()}")
                    print(Fore.GREEN + f"The searched ID is associated with: {associated_id}")
                    print(Fore.BLUE + "Here is the direct link to the file:")
                    print(Fore.YELLOW + associated_file_path)  # This may become a clickable link in some terminals
                    file_found = True
                    break  # Break the loop if the ID is found
        except FileNotFoundError:
            print(Fore.RED + f"File not found: {file_path}")
        except json.JSONDecodeError:
            print(Fore.RED + f"Could not parse JSON from file: {file_path}")

        if file_found:
            break  # Break the outer loop if the ID is found

    if not file_found:
        print(Fore.RED + "ID not found in any of the provided JSON files.")

#Main Menu Principal
def main_menu():
    while True:
        print(f"{Fore.RED}\nNasa get Hacked by Kaichi-Sama {Fore.GREEN}for question dm Discord : kaichisama.{Style.RESET_ALL}")
        print(f"{Fore.LIGHTMAGENTA_EX}Join : https://discord.gg/7KprcpxhEH{Style.RESET_ALL}")
        print(f"{Fore.LIGHTMAGENTA_EX}Powered by Kawaii Squad Devs : Kaichi-Sama / >_Unknown User{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}♥ Kaichi-Sama Menu UwU ♥{Style.RESET_ALL}:")
        print("1. Local Database")
        print(f"2. Network Database {Fore.RED}Not Finished Need an other Dev for fix it Thanks <3{Style.RESET_ALL}")
        print("3. Start The Logger")
        print(f"{Fore.RED}4. DON'T CLICK HERE{Style.RESET_ALL}")  # Option 6 en rouge
        print("5. Exit")  # Mettez à jour le numéro des options ici
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
        elif choice == "5":  # Mettez à jour le numéro de sortie ici
            print("\nHave Sex with Me!")
            break
        else:
            print("Invalid option, please try again.")
#Local Database Menu
def local_database_menu():
    while True:
        print("\nLocal Database Menu:")
        print("1. Display All IDs in Cache")
        print("2. Research an ID in Cache")
        print("3. Filtered Local Research")
        print("4. Research an ID in LocalDatabase")  # Nouvelle option ajoutée ici
        print("5. Back to Main Menu")

        choice = input("Choose an option: ")

        if choice == "1":
            # Remplacez 'display_all_ids_in_cache' par le nom réel de votre fonction
            display_all_ids_in_cache()
        elif choice == "2":
            search_id = input("\nEnter the ID you want to research in cache: ")
            search_in_cache(search_id)
        elif choice == "3":
            print("\nSub-Menu:")
            print("1. Display World Info")
            print("2. Display Avatar Info")
            sub_choice = input("Choose an option: ")

            if sub_choice == "1":
                display_world_info()
            elif sub_choice == "2":
                display_ids_filtered("Avatar")
            else:
                print("Invalid option, please try again.")
        elif choice == "4":  # Nouveau cas pour la nouvelle option
            search_id = input("\nEnter the ID you want to research in the LocalDatabase: ")
            research_id_in_local_database(search_id)  # Fonction à définir
        elif choice == "5":
            break
        else:
            print("Invalid option, please try again.")
#pas finit
def Network_database_menu():   
    while True:
        print("\nNetwork Database Menu:")
        print("1. ")
        print("2. Research an ID in Network Database")
        print("3. ")
        print("4. Filtered Network Research")
        print("5. Back to Main Menu")

        choice = input("Choose an option: ")

        if choice == "1":
            display_all_ids()
        elif choice == "2":
            search_id = input("\nEnter the ID you want to search for: ")
            search_in_cache(search_id)
        elif choice == "3":
            search_id = input("\nEnter the ID you want to search for: ")
            search_id_in_database(search_id)
        elif choice == "4":
            print("\nSub-Menu:")
            print("1. Display World Info")
            print("2. Display Avatar Info")
            sub_choice = input("Choose an option: ")

            if sub_choice == "1":
                display_world_info()
            elif sub_choice == "2":
                display_ids_filtered("Avatar")
            else:
                print("Invalid option, please try again.")
        elif choice == "5":
            break
        else:
            print("Invalid option, please try again.")
#fait un RickRoll
def rickroll():
    url = 'https://youtu.be/a3Z7zEc7AXQ'
    wb.open(url)

def get_vrchat_friends():
    # Check if the auth cookie file exists
    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, 'r') as file:
            cookie_content = file.read().strip()
            # Extract the 'auth' cookie value
            auth_cookie = next((part.split('=')[1] for part in cookie_content.split('; ') if part.startswith('auth=')), None)
            if not auth_cookie:
                print("Auth cookie value not found in the file.")
                return None
    else:
        print("Auth cookie file not found. Please log in first.")
        return None

    # Set the request URL
    url = "https://api.vrchat.cloud/api/1/auth/user/friends?offline=true"
    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    # Make the HTTP request
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        # Process the friends list
        friends_list = response.json()
        # For example, save it to a file
        with open('logs/friendslist.json', 'w') as file:
            json.dump(friends_list, file, indent=4)
        print("Friends list saved.")
        return friends_list
    else:
        # Handle errors
        print(f"Error retrieving friends list: {response.status_code}")
        return None

if __name__ == "__main__":
    check_for_updates()
    login_and_save_auth_cookie()
    save_vrchat_user_id()
    get_vrchat_friends()
    main_menu()