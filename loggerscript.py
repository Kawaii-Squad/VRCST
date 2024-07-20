import os
import shutil
import datetime
import time
import hashlib
import json
import requests
import ctypes
import logging
import UnityPy
from collections import defaultdict

def create_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {directory}. Error message: {e}")

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
auth_cookie = get_auth_cookie(auth_cookie_path)
# Chemins constants
user_directory = os.path.expanduser("~")
LOGS_PATH = os.path.join(user_directory, "Logs")
PATH = os.path.join(user_directory, "AppData", "LocalLow", "VRChat", "VRChat", "Cache-WindowsPlayer")

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

start_the_logger(PATH)
