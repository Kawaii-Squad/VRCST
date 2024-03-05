import os, re, sys, shutil, datetime, time, logging, hashlib, base64, json, subprocess, requests
from getpass import getpass
from collections import defaultdict
from urllib.request import Request
import traceback, pyfiglet, webbrowser as wb, UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.classes.Object import NodeHelper
import keyboard, vrchatapi
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
import threading, ctypes

#Notification Windows
def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name='VRCST',  # Nom de votre application
        app_icon=None,  # Chemin vers l'icône de l'application (si nécessaire)
        timeout=10  # Durée en secondes pendant laquelle la notification est affichée
    )

# Chemins constants
user_directory = os.path.expanduser("~")
LOGS_PATH = os.path.join(user_directory, "Logs")
PATH = os.path.join(user_directory, "AppData", "LocalLow", "VRChat", "VRChat", "Cache-WindowsPlayer")

# VERSION DU LOGICIEL :
version = "1.1.0"

#AuthCookie
def get_auth_cookie(auth_cookie_path):
    # Vérifier si le fichier existe
    if os.path.exists(auth_cookie_path):
        # Lire le contenu du fichier
        with open(auth_cookie_path, 'r') as file:
            cookie_content = file.read().strip()

            # Extraire la valeur du cookie 'auth'
            auth_cookie = next((part.split('=')[1] for part in cookie_content.split('; ') if part.startswith('auth=')), None)

            # Vérifier si la valeur a été trouvée
            if auth_cookie:
                return auth_cookie
            else:
                return None
    else:
        return None
#Username Saver
def get_display_name():
    # Check if user_id_file exists
    if not os.path.exists(user_id_file):
        print(f"User ID file not found: {user_id_file}")
        return None

    # Load user ID from the file
    with open(user_id_file, 'r') as file:
        user_id = file.read().strip()

    # API endpoint URL
    url = f"https://api.vrchat.cloud/api/1/users/{user_id}"

    # Headers and cookies
    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    # Make the GET request
    response = requests.get(url, headers=headers, cookies=cookies)

    # Check the response status code
    if response.status_code == 200:
        user_info = response.json()

        if isinstance(user_info, list) and user_info:  # Check if user_info is a non-empty list
            return user_info[0].get('displayName')
        elif isinstance(user_info, dict):  # Check if user_info is a dictionary
            return user_info.get('displayName')
        else:
            print("Unexpected response format:", user_info)
            return None
    else:
        print(f"Error retrieving user information: {response.status_code}")
        return None

# Définition du chemin local du script
local_script_path = "VRCST.py"
user_id_file = 'LocalDB/temps/user_id.bin'  # Nom du fichier pour enregistrer le user ID
user_agent = 'VRC Scanner Tool / Kawaii Squad Studio'
auth_cookie_path = 'LocalDB/temps/AuthCookie.bin'
friendlist = 'LocalDB/infos/friendslist.json'
auth_cookie = get_auth_cookie(auth_cookie_path)
displayName = get_display_name()
# Configuration VRChat
IP_VRCHAT = "127.0.0.1"  # Adresse IP de votre instance VRChat
PORT_VRCHAT_SEND = 9000  # Port d'envoi OSC de VRChat

#INTERNAL FONCTIONS
def create_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {directory}. Error message: {e}")

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

def run_as_admin(script_path):
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        # Restart the script with administrator privileges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)
        sys.exit()
    else:
        print("The script is already running with administrator privileges.")

#Fancy Welcome
def fancy_welcome(version, developers=None):
    if developers is None:
        developers = [
            {'name': 'Kaichi-Sama', 'role': 'Lead Developer'},
            {'name': 'ChatGPT', 'role': 'ALL Developer'}
        ]

    # ASCII Art text for "Welcome to Kawaii Squad"
    welcome_text = r"""

 /$$    /$$ /$$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$$$                                                            
| $$   | $$| $$__  $$ /$$__  $$ /$$__  $$|__  $$__/                                                            
| $$   | $$| $$  \ $$| $$  \__/| $$  \__/   | $$                                                               
|  $$ / $$/| $$$$$$$/| $$      |  $$$$$$    | $$                                                               
 \  $$ $$/ | $$__  $$| $$       \____  $$   | $$                                                               
  \  $$$/  | $$  \ $$| $$    $$ /$$  \ $$   | $$                                                               
   \  $/   | $$  | $$|  $$$$$$/|  $$$$$$/   | $$                                                               
    \_/    |__/  |__/ \______/  \______/    |__/           
                                                    
                                                                                                               
    """

    # Thank you message
    thank_you_text = "Thank you for using the Kawaii VRC Scanner Tool"

    # Version Box
    version_box = f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                    Version: {version:<}                                ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

    # Print the welcome message
    print(welcome_text)
    # Print the thank you message
    print(thank_you_text)
    # Print the version box
    print(version_box)

    # Heading for the developers section
    developers_heading = "Developers and Contributors"
    # Start of the box
    print("+" + "-" * 76 + "+")
    # Heading
    print(f"|{developers_heading.center(76)}|")
    # Separator
    print("+" + "-" * 76 + "+")
    # List each developer and their role
    for dev in developers:
        name = dev.get('name', 'Unknown')
        role = dev.get('role', 'Contributor')
        # Creating the entry
        dev_entry = f"| {name} - {role.ljust(60)} |"
        # Print the entry
        print(dev_entry)
    # End of the box
    print("+" + "-" * 76 + "+")

#The File Updater
def update_files():
    # Dictionnaire des fichiers à mettre à jour
    files_to_update = {
        "VRChatScanner.py": "https://raw.githubusercontent.com/Kawaii-Squad/VRCST/main/VRChatScanner.py",
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

#Login Script
def login_and_save_auth_cookie():
    print("Welcome to the VRChat login script!")

    # Check if AuthCookie file exists and is valid
    if os.path.exists(auth_cookie_path):
        with open(auth_cookie_path, "r") as f:
            content = f.read()

        # Extract authCookie and twoFactorAuth from the file content
        auth_cookie = None
        two_factor_auth = None
        for line in content.split(';'):
            if line.startswith('auth='):
                auth_cookie = line[len('auth='):]
            elif line.startswith('twoFactorAuth='):
                two_factor_auth = line[len('twoFactorAuth='):]

        if auth_cookie and not two_factor_auth:
            # Perform a GET request to validate the existing authCookie
            try:
                response = validate_auth_cookie(auth_cookie)
                if response.status_code == 200:
                    print("\033[92mLogged in with existing authCookie.\033[0m")
                    save_vrchat_user_id()
                    print("\033[92mLogged as:", displayName, "\033[0m")
                    return
            except Exception as e:
                print(f"Error validating existing authCookie: {e}")

    # If the existing authCookie is invalid or not found, proceed with login
    perform_login()

def validate_auth_cookie(auth_cookie, current_user=None):
    url = "https://api.vrchat.cloud/api/1/auth"
    headers = {
        "Cookie": f"amplitude_id_a750df50d11f21f712262cbd4c0bab37vrchat.com=string; auth={auth_cookie}",
        "User-Agent": user_agent  # Assuming user_agent is defined elsewhere
    }

    print(f"Sending test request to {url} with headers: {headers}")
    response = requests.get(url, headers=headers)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    return response

def perform_login():
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
                return
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
                return

        print("\033[92mLogged in as:", current_user.display_name + "\033[0m")
        show_notification('Connecté avec Succès', 'L\'utilisateur est connecté avec succès.')
        cookies = api_client.rest_client.cookie_jar
        mock_request_object = Request(url="https://api.vrchat.cloud/api/1/auth/user", method="GET")
        cookies.add_cookie_header(mock_request_object)
        auth_cookie = mock_request_object.get_header("Cookie")

        os.makedirs("LocalDB/temps", exist_ok=True)

        with open(auth_cookie_path, "wb") as f:
            f.write(auth_cookie.encode())
        print("Authentication cookie saved in AuthCookie.bin")

        # Enregistrez le User ID après la connexion réussie
        save_vrchat_user_id()

#VRC-OSC
def send_osc_message(address, *args):
    client = udp_client.SimpleUDPClient(IP_VRCHAT, PORT_VRCHAT_SEND)
    client.send_message(address, args)

def advertise_kawaii_gang():
    kawaii_frames = [
        "🌈 Thanks for using Kawaii Squad Script 🌸",
        "🌟 Discover amazing assets with us! ✨",
        "🎉 Visit our community for free leaks! 🎊",
        "🌈 Join Kawaii Squad Free! 🌸"
    ]

    # Adresse OSC pour envoyer un message au chatbox de VRChat
    chatbox_address = "/chatbox/input"

    for frame in kawaii_frames:
        send_osc_message(chatbox_address, frame)
        time.sleep(2)

#UserID Saver
def save_vrchat_user_id():
    url = "https://api.vrchat.cloud/api/1/auth/user"
    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        user_info = response.json()
        user_id = user_info.get('id')

        # Save the user ID in the specified file in the Logs directory
        with open(os.path.join(user_id_file), 'wb') as file:
            file.write(user_id.encode('utf-8'))  # Corrected this line

        print("User ID successfully saved in the logs directory.")
        return True
    else:
        print(f"Error retrieving user information: {response.status_code}")
        return False

#LOGGER
def download_entity_image(entity_id, entity_type):
    logging.basicConfig(filename='LocalDB/temps/download_log.log', level=logging.INFO, format='%(asctime)s %(message)s')

    # Construire le chemin du fichier en fonction du type d'entité
    file_path = f'LocalDB/infos/INFO_{entity_type}.json'

    # Vérifier l'existence du fichier
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found.")
        return

    # Charger les données du fichier
    with open(file_path, 'r') as file:
        try:
            entities_info = json.load(file)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to load JSON from {file_path}: {e}")
            return

    # Rechercher l'entité par ID et télécharger l'image
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
    # Définir l'URL de la requête
    url = f"https://api.vrchat.cloud/api/1/{'avatars' if id_type == 'VRCA' else 'worlds'}/{id_}" if id_type in ['VRCA', 'VRCW'] else None

    if not url:
        print(f"Unsupported ID type: {id_type}")
        return None

    headers = {"User-Agent": user_agent}
    cookies = {"auth": auth_cookie}

    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        try:
            # Essayer de convertir la réponse en JSON
            data = response.json()
        except json.decoder.JSONDecodeError:
            # Gérer le cas où la réponse n'est pas un JSON valide
            print(f"Error decoding JSON response for {id_type} ID {id_}. Response content: {response.text}")
            return None

        data_file_path = 'LocalDB/temps/Temp_data.json'  # Mise à jour ici
        existing_data = {}

        # Ajouter ou mettre à jour les informations de l'ID dans les données existantes
        if os.path.exists(data_file_path):
            try:
                with open(data_file_path, 'r') as file:
                    existing_data = json.load(file)
            except json.decoder.JSONDecodeError:
                # Gérer le cas où le fichier est vide ou ne contient pas de données JSON valides
                print(f"Error decoding existing data from {data_file_path}. File content: {file.read()}")
                existing_data = {}

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
        try:
            with open(file_path, 'r') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            # Si le fichier ne contient pas du JSON valide, initialiser avec une liste vide
            existing_data = []
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

                                # Déterminez le type d'entité et le chemin de log approprié
                                entity_type = 'VRCA' if blueprint_id.startswith('avtr_') else 'VRCW'
                                log_path = os.path.join("LocalDB", "infos", f"ID_REF_{entity_type.upper()}.json")
                                info_path = os.path.join("LocalDB", "infos", f"INFO_{entity_type.upper()}.json")
                                target_path = os.path.join("LocalDB", entity_type, f"{blueprint_id}.{entity_type.lower()}")

                                info = get_info_id(blueprint_id, entity_type)  # Appeler d'abord get_info_id

                                file_hash = hash_file(filepath)
                                is_duplicate = update_log_data(log_path, file_hash, blueprint_id, target_path)

                                if not os.path.exists(target_path) and not is_duplicate:
                                    shutil.copy(filepath, target_path)
                                    print(f"{datetime.datetime.now()} - {Fore.GREEN}{entity_type} Added Successfully: {blueprint_id}{Style.RESET_ALL}")

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

#LOCAL DATABASE (NOT FINISH)  
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

#NETWORK DATABASE
def launch_friendlistsaver():
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Change the current working directory to the script directory
        os.chdir(script_dir)
        
        # Construct the path to friendlistsaver.py
        friendlistsaver_path = os.path.join("Dependencies", "subscripts", "friendlistsaver.py")

        # Check if the file exists before launching
        if os.path.isfile(friendlistsaver_path):
            # Launch friendlistsaver.py with admin privileges
            if run_as_admin(friendlistsaver_path):
                return
        else:
            print(f"The specified file is not found: {friendlistsaver_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
#GUI
def main_menu():
    while True:
        print(f"{Fore.RED}\nNasa got Hacked by Kaichi-Sama {Fore.GREEN}for question dm Discord : kaichisama.{Style.RESET_ALL}")
        print(f"{Fore.LIGHTMAGENTA_EX}Join : https://discord.gg/7KprcpxhEH{Style.RESET_ALL}")
        print(f"{Fore.LIGHTMAGENTA_EX}Powered by Kawaii Squad Devs : Kaichi-Sama / >_Unknown User{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}♥ Kaichi-Sama Menu UwU ♥{Style.RESET_ALL}:")
        print("1. Local Database")
        print(f"2. Network Database {Fore.RED}Not Finished Need an other Dev for fix it Thanks <3{Style.RESET_ALL}")
        print("3. Start The Logger")
        print(f"{Fore.RED}4. DON'T CLICK HERE{Style.RESET_ALL}")  # Option 4 en rouge
        print("5. Exit")  # Mettez à jour le numéro des options ici
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
            launch_friendlistsaver()
        else:
            print("Invalid option, please try again.")

def local_database_menu():
    while True:
        print("\nLocal Database Menu:")
        print("1. Display All IDs in Cache")
        print("2. Filtered Local Research")
        print("3. Research an ID in LocalDatabase")  # Nouvelle option ajoutée ici
        print("4. Back to Main Menu")

        choice = input("Choose an option: ")

        if choice == "1":
            # Remplacez 'display_all_ids_in_cache' par le nom réel de votre fonction
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
        elif choice == "3":  # Nouveau cas pour la nouvelle option
            search_id = input("\nEnter the ID you want to research in the LocalDatabase: ")
            research_id_in_local_database(search_id)  # Fonction à définir
        elif choice == "4":
            break
        else:
            print("Invalid option, please try again.")


#fait un RickRoll

def rickroll():
    url = 'https://youtu.be/a3Z7zEc7AXQ'
    wb.open(url)

update_files()
fancy_welcome(version)
advertise_kawaii_gang()
login_and_save_auth_cookie()
main_menu()
