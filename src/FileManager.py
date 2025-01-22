import json
import os
import Connection
import Manager

class NETWORK:
    NAME = "Name"
    PINNED_MESSAGES = "Pinned Messages"
    CHANNELS = "Channels"

class FOLDER:
    DATA = "data"
    SRC = "src"

class FILE:
    NETWORK_FILE = "network"
    MANAGER = "manager"
    MESSAGE_PACKAGES_FILE = "message_packages"

class MANAGER:
    NETWORKS = "Networks"
    BANNED = "Banned"
    COUNTER = "Counter"

class MESSAGE_PACKAGE:
    ORIGINAL_SINGULAR_MESSAGE = "OSM"
    RELAYED_SINGULAR_MESSAGES = "RSMs"
    VOLUNTEER_ORIGINAL_MESSAGE_IDS = "VOMIS"

class SINGULAR_MESSAGE:
    CHANNEL_ID = "Channel ID"
    MESSAGE_ID = "Message ID"
    JUMP_URL = "Jump URL"

class CONNECTION:
    CONNECTION_NAME = "Connection Name"
    SERVER_ID = "Server ID"
    WEBHOOK_ID = "Webhook ID"
    CHANNEL_ID = "Channel ID"
    SERVER_ACRONYM = "Servery Acronym"
    LEVEL = "Level"
    MESSAGE_REFERENCES = "Message References"

class BAN:
    SERVER_NAME = "Server Name"
    SERVER_USERNAME = "Server Username"
    USER_ID = "User ID"
    SERVER_LEVEL = "Server Level"
    BAN_CODE = "Ban Code"

CONNECTY_FD = os.path.join(os.getcwd(), FOLDER.DATA)
print(CONNECTY_FD)
print("TIP: does the current directory make sense?")

def file_exists(folder_name, file_name):
    try:
        with open(os.path.join(CONNECTY_FD, folder_name, file_name + ".json"), 'r') as file:
            file.close()
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(str(e))

def create_connection_folder(folder_name):
    try:
        os.mkdir(os.path.join(CONNECTY_FD, folder_name))
    except FileExistsError:
        return

def folder_check():
    if os.path.isdir(CONNECTY_FD):
        return
    else:
        try:
            os.mkdir(os.path.join(CONNECTY_FD))
        except FileExistsError:
            return

def manager_file_exists():
    try:
        with open(os.path.join(CONNECTY_FD, FILE.MANAGER + ".json"), 'r') as file:
            file.close()
        return True
    except FileNotFoundError:
        return False

def delete_network(network):
    try:
        for file in os.listdir(os.path.join(CONNECTY_FD, network.name)):
            os.remove(os.path.join(CONNECTY_FD, network.name, file))
        os.rmdir(os.path.join(CONNECTY_FD, network.name))
    except FileNotFoundError:
        return

def get_json_connection_files(network):
    try:
        files = os.listdir(os.path.join(CONNECTY_FD, network.name))
        connection_files = list()
        for file in files:
            if file.endswith(".json"):
                file_name = file[:len(file) - 5]
                if os.path.isfile(os.path.join(CONNECTY_FD, network.name, file_name + ".json")):
                    if file_name != FILE.NETWORK_FILE and file_name != FILE.MESSAGE_PACKAGES_FILE:
                        connection_files.append(file_name)
        return connection_files
    except FileNotFoundError:
        return list()

def delete_connection_data(network, channel_id: int):
    try:
        os.remove(os.path.join(CONNECTY_FD, network.name, str(channel_id) + ".json"))
    except FileNotFoundError:
        return

def save_manager_data():
    with open(os.path.join(CONNECTY_FD, FILE.MANAGER + ".json"), 'w') as file:
        json.dump(Manager.create_dict(), file, indent=2)
        file.close()

def retrieve_manager_data():
    with open(os.path.join(CONNECTY_FD, FILE.MANAGER + ".json"), 'r') as file:
        return json.load(file)

def save_network_list(network):
    create_connection_folder(network.name)
    with open(os.path.join(CONNECTY_FD, network.name, FILE.NETWORK_FILE + ".json"), 'w') as file:
        print(network.create_network_dict())
        json.dump(network.create_network_dict(), file, indent=2)
        file.close()

def retrieve_network_list(network):
    with open(os.path.join(CONNECTY_FD, network.name, FILE.NETWORK_FILE + ".json"), 'r') as file:
        return json.load(file)

def save_network_packages(network):
    create_connection_folder(network.name)
    with open(os.path.join(CONNECTY_FD, network.name, FILE.MESSAGE_PACKAGES_FILE + ".json"), 'w') as file:
        json.dump(network.create_message_pacakge_dict(), file, indent=2)
        file.close()

def retrieve_network_packages(network):
    with open(os.path.join(CONNECTY_FD, network.name, FILE.MESSAGE_PACKAGES_FILE + ".json"), 'r') as file:
        return json.load(file)

def save_connection_data(folder_name: str, connection: Connection.Connection):
    create_connection_folder(folder_name)
    with open(os.path.join(CONNECTY_FD, folder_name, str(connection.channel.id) + ".json"), 'w') as file:
        json.dump(connection.create_dict(), file, indent=2)
        file.close()

def retrieve_connection_data(folder_name: str, channel_id: int):
    with open(os.path.join(CONNECTY_FD, folder_name, str(channel_id) + ".json"), 'r') as file:
        return json.load(file)
