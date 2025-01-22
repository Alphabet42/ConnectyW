import discord
import Network
import logging
import Banned
import unicodedata
import Utilities as ult
import FileManager as FM
import ConnectyException

class Manager:
    is_loaded = False
    networks = list()
    banned = dict()
    counter = 1000
    client: discord.Client
    OFFICIAL_WEBHOOK_NAME = "ConnectyW"

def create_dict():
    network_names = list()
    for network in Manager.networks:
        network_names.append(network.name)

    banned_list = list()
    for ban_code in Manager.banned:
        banned = Manager.banned[ban_code]
        banned_list.append(banned.create_dict())

    return {
        FM.MANAGER.NETWORKS: network_names,
        FM.MANAGER.BANNED: banned_list,
        FM.MANAGER.COUNTER: Manager.counter
    }

async def load_manager():
    Manager.networks.clear()
    Manager.banned.clear()

    if FM.manager_file_exists():
        _manager_dict = FM.retrieve_manager_data()

        _networks_list = _manager_dict[FM.MANAGER.NETWORKS]
        for _network in _networks_list:
            network = Network.Network(_network)
            Manager.networks.append(network)

        _banned_list = _manager_dict[FM.MANAGER.BANNED]

        for _banned_dict in _banned_list:
            banned = Banned.BannedUser(_banned_dict[FM.BAN.SERVER_NAME],
                                       _banned_dict[FM.BAN.SERVER_USERNAME],
                                       _banned_dict[FM.BAN.USER_ID],
                                       _banned_dict[FM.BAN.SERVER_LEVEL],
                                       _banned_dict[FM.BAN.BAN_CODE])

            Manager.banned[_banned_dict[FM.BAN.BAN_CODE]] = banned

        Manager.counter = _manager_dict[FM.MANAGER.COUNTER]

        # Load Networks
        for network in Manager.networks:
            await network.load_network()

def save_manager():
    FM.save_manager_data()
    for network in Manager.networks:
        FM.save_network_list(network)
        FM.save_network_packages(network)
        for channel_id in network.connections:
            connection = network.connections[channel_id]
            FM.save_connection_data(network.name, connection)
    print("Database Saved")

def add_network(network_name: str):
    network = Network.Network(network_name)
    Manager.networks.append(network)
    FM.save_manager_data()

def remove_network(network_name: str):
    target_network = None
    for network in Manager.networks:
        if network.name == network_name:
            target_network = network

    if target_network is None:
        raise ConnectyException.UnknownIdentification("Unknown Network")

    # Delete Data
    Manager.networks.remove(network)
    network.connections.clear()
    network.active_connections.clear()
    network.message_packages.clear()
    FM.delete_network(network)
    del network

    FM.save_manager_data()

def get_network_by_id(target_channel_id: int):
    for network in Manager.networks:
        for channel_id in network.active_connections:
            if channel_id == target_channel_id:
                return network
    raise ConnectyException.UnknownIdentification("Unknown Channel")

def raw_get_network_by_id(target_channel_id: int):
    for network in Manager.networks:
        for connection in FM.get_json_connection_files(network):
            if int(connection) == target_channel_id:
                return network
    raise ConnectyException.UnknownIdentification("Unknown Channel")

def get_network_by_name(name: str):
    for network in Manager.networks:
        if network.name == name:
            return network
    raise ConnectyException.UnknownIdentification("Unknown Network")

async def printb(interaction: discord.Interaction):
    # Formatting
    server_name_spacing = "                                 "
    display_name_spacing = "                       "
    FORMAT = "| {0} | {1} | {2} |\n"
    LINE_DIVIDER = "|--------------------------------------------------------------------|\n"

    # Header
    output =  "[Banned.txt]                                                 [-][□][x]\n"
    output += "|--------------------------------------------------------------------|\n"
    output += "|           Server Origin           |   Server Display Name   | Code |\n"
    output += "|--------------------------------------------------------------------|\n"

    for ban_code in Manager.banned:
        banned = Manager.banned[ban_code]
        server_name = auto_strip(server_name_spacing, banned.server_name)
        display_name = auto_strip(display_name_spacing, banned.server_username)
        output += FORMAT.format(server_name, display_name, banned.ban_code)
        output += LINE_DIVIDER

    if len(Manager.banned) == 0:
        output += "| EMPTY                                                              |\n"
        output += LINE_DIVIDER

    try:
        await interaction.user.send(content="{0}{1}{2}".format("```", output, "```"))
    except discord.DiscordException:
        return

async def printd(interaction: discord.Interaction):
    # Formatting
    direct_spacing = "                                                               "
    normal_spacing = "                                                                  "
    NORMAL_FORMAT = "| {0} |\n"
    DIRECT_FORMAT = "|  ∟ {0} |\n"
    LINE_DIVIDER =  "|--------------------------------------------------------------------|\n"

    # Header One
    output =  "[Data.txt]                                                   [-][□][x]\n".format(interaction.user.name)
    output += "|--------------------------------------------------------------------|\n"
    output += "|                               Manager                              |\n"
    output += "|--------------------------------------------------------------------|\n"

    # List Networks
    if len(Manager.networks) != 0:
        output += NORMAL_FORMAT.format(auto_strip(normal_spacing, "Networks"))
        for network in Manager.networks:
            output += DIRECT_FORMAT.format(auto_strip(direct_spacing, network.name))
    else:
        output += NORMAL_FORMAT.format(auto_strip(normal_spacing, "Networks [EMPTY]"))

    # Show banned count
    output += NORMAL_FORMAT.format(auto_strip(normal_spacing, "Banned: {0}".format(str(len(Manager.banned)))))

    # Header Two
    output += "|--------------------------------------------------------------------|\n"
    output += "|                               Networks                             |\n"
    output += "|--------------------------------------------------------------------|\n"

    # List connection info of each network and total messages
    if len(Manager.networks) != 0:
        for network in Manager.networks:
            output += NORMAL_FORMAT.format(auto_strip(normal_spacing, "[{0}]".format(network.name)))
            for connection_id in network.connections:
                connection = network.connections[connection_id]
                channel = connection.channel
                connection_info = channel.name + " [{0}]".format(str(connection.level)) + " in " + channel.guild.name
                output += DIRECT_FORMAT.format(auto_strip(direct_spacing, connection_info))
            messages_section = "Total Messages: {0}".format(str(len(network.message_packages)))
            output += NORMAL_FORMAT.format(auto_strip(normal_spacing, messages_section))
            output += LINE_DIVIDER
    else:
        output += NORMAL_FORMAT.format(normal_spacing, "EMPTY")
        output += LINE_DIVIDER

    try:
        await interaction.user.send(content="{0}{1}{2}".format("```", output, "```"))
    except discord.DiscordException:
        return

def auto_strip(spacing: str, text: str):
    maximum_length = len(spacing)
    modified_text = str()

    # Do not include Emojis
    for char in text:
        if char.isascii():
            modified_text += char

    if len(modified_text) >= maximum_length:
        fixed_text = modified_text[0:maximum_length - 3]
        fixed_text += "..."
    else:
        spacing = spacing[:-len(modified_text)]
        fixed_text = modified_text + spacing
    return fixed_text

async def ban(interaction: discord.Interaction, target_message_id: int):
    try:
        network = get_network_by_id(interaction.channel_id)
        this_channel = network.connections[interaction.channel_id]
    except (KeyError, ConnectyException.UnknownIdentification):
        raise ConnectyException.UnknownIdentification("Irrelevant Channel")
    try:
        target_message_package = this_channel.message_log[target_message_id]
        original_singular_message = target_message_package.original_singular_message
        original_channel = network.connections[original_singular_message.channel_id]
    except KeyError:
        raise ConnectyException.UnknownIdentification("Unknown Message ID")

    # Don't ban if current server level is too low
    if this_channel.level < original_channel.level:
        raise ConnectyException.ConnectyActionFailed("Insufficient Level")

    try:
        original_message = await original_channel.channel.fetch_message(original_singular_message.message_id)
    except (discord.NotFound, discord.HTTPException):
        raise ConnectyException.ConnectyActionFailed("Failed. Try Again")

    # Check if person is already banned'
    ban_exists = False
    for ban_code in Manager.banned:
        banned = Manager.banned[ban_code]
        if banned.user_id == interaction.user.id:
            ban_exists = True
    if ban_exists:
        raise ConnectyException.ConnectyAlreadyDone("Already Banned")

    # Generate new ban code
    ban_code = ult.generate_code()

    # Add it to list of banned users
    banned_user = Banned.BannedUser(original_message.guild.name,
                                    original_message.author.display_name,
                                    original_message.author.id,
                                    original_channel.level,
                                    ban_code)

    Manager.banned[ban_code] = banned_user
    FM.save_manager_data()

def unban(interaction: discord.Interaction, ban_code: int):
    try:
        network = get_network_by_id(interaction.channel_id)
        this_connection = network.connections[interaction.channel_id]
    except (KeyError, ConnectyException.UnknownIdentification):
        raise ConnectyException.UnknownIdentification("Irrelevant Channel")
    try:
        banned = Manager.banned[ban_code]
    except KeyError:
        raise ConnectyException.UnknownIdentification("Unknown Ban")

    if this_connection.level >= banned.server_level:
        Manager.banned.pop(ban_code)
    else:
        raise ConnectyException.ConnectyActionFailed("Insufficient Level")


