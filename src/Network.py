import Manager as MNG
import FileManager as FM
import SingularMessage as SM
import MessagePackage as MP
import Connection
import discord
import logging
import Utilities as ult
import ConnectyException

class Network:
    def __init__(self, name: str):
        self.name = name
        self.message_packages = dict()
        self.active_connections = list()
        self.connections = dict()

    def create_network_dict(self):
        return {
            FM.NETWORK.NAME: self.name,
            FM.NETWORK.CHANNELS: self.active_connections
        }

    def create_message_pacakge_dict(self):
        message_packages_dict = dict()
        for original_message_id in self.message_packages:
            message_package = self.message_packages[original_message_id]
            message_packages_dict[original_message_id] = message_package.create_dict()
        return message_packages_dict

    async def load_network(self):
        """
        Load the message packages
        Automatically annex with pre-existing data
        """
        if FM.file_exists(self.name, FM.FILE.MESSAGE_PACKAGES_FILE):
            _message_packages_list = FM.retrieve_network_packages(self)
            self.message_packages.clear()

            # Get a hold of all the message packages
            for _message_package_id in _message_packages_list:
                _message_package = _message_packages_list[_message_package_id]
                _original_singular_message = _message_package[FM.MESSAGE_PACKAGE.ORIGINAL_SINGULAR_MESSAGE]
                _relayed_singular_messages = _message_package[FM.MESSAGE_PACKAGE.RELAYED_SINGULAR_MESSAGES]
                _volunteer_original_message_ids = _message_package[FM.MESSAGE_PACKAGE.VOLUNTEER_ORIGINAL_MESSAGE_IDS]

                original_singular_message = SM.SingularMessage(
                    _original_singular_message[FM.SINGULAR_MESSAGE.CHANNEL_ID],
                    _original_singular_message[FM.SINGULAR_MESSAGE.MESSAGE_ID],
                    _original_singular_message[FM.SINGULAR_MESSAGE.JUMP_URL])

                relayed_singular_messages = []
                for _relayed_singular_message in _relayed_singular_messages:
                    relayed_singular_message = SM.SingularMessage(
                        _relayed_singular_message[FM.SINGULAR_MESSAGE.CHANNEL_ID],
                        _relayed_singular_message[FM.SINGULAR_MESSAGE.MESSAGE_ID],
                        _relayed_singular_message[FM.SINGULAR_MESSAGE.JUMP_URL])
                    relayed_singular_messages.append(relayed_singular_message)

                message_package = MP.MessagePackage(original_singular_message, relayed_singular_messages)

                # Does not give actual message packages. All message packages are not available yet.
                message_package.volunteer_message_packages = _volunteer_original_message_ids

                # Save to global message package storage
                self.message_packages[original_singular_message.message_id] = message_package

            # Fulfill Volunteer Packages
            for original_message_id in self.message_packages:
                message_package = self.message_packages[original_message_id]
                _volunteer_original_message_ids = message_package.volunteer_message_packages

                volunteer_message_packages = []
                for _volunteer_original_message_id in _volunteer_original_message_ids:
                    volunteer_message_package = self.message_packages[_volunteer_original_message_id]
                    volunteer_message_packages.append(volunteer_message_package)

                message_package.volunteer_message_packages.clear()
                message_package.volunteer_message_packages = volunteer_message_packages

        # Automatically annex servers along with its data
        if FM.file_exists(self.name, FM.FILE.NETWORK_FILE):
            _network = FM.retrieve_network_list(self)
            _network_name = _network[FM.NETWORK.NAME]
            _network_list = _network[FM.NETWORK.CHANNELS]

            for channel_id in _network_list:
                if FM.file_exists(self.name, str(channel_id)):
                    _server_data_dict = FM.retrieve_connection_data(self.name, channel_id)
                    _server_id = _server_data_dict[FM.CONNECTION.SERVER_ID]
                    _webhook_id = _server_data_dict[FM.CONNECTION.WEBHOOK_ID]
                    _channel_id = _server_data_dict[FM.CONNECTION.CHANNEL_ID]
                    _server_acronym = _server_data_dict[FM.CONNECTION.SERVER_ACRONYM]
                    _level = _server_data_dict[FM.CONNECTION.LEVEL]
                    _message_references = _server_data_dict[FM.CONNECTION.MESSAGE_REFERENCES]

                    chosen_channel = MNG.Manager.client.get_channel(channel_id)
                    chosen_webhook = None

                    # Prioritize finding exact webhook first
                    webhooks = await chosen_channel.webhooks()

                    for webhook in webhooks:
                        if webhook.name == MNG.Manager.OFFICIAL_WEBHOOK_NAME and webhook.id == _webhook_id:
                            chosen_webhook = webhook

                    for webhook in webhooks:
                        if webhook.name == MNG.Manager.OFFICIAL_WEBHOOK_NAME and chosen_webhook is None:
                            chosen_webhook = await chosen_channel.create_webhook(name=MNG.Manager.OFFICIAL_WEBHOOK_NAME)

                    if chosen_webhook is None:
                        chosen_webhook = await chosen_channel.create_webhook(name=MNG.Manager.OFFICIAL_WEBHOOK_NAME)

                    # Instantiate Server Object
                    connection = Connection.Connection(_server_id, chosen_webhook, chosen_channel, _server_acronym, _level)

                    # Add Message Packages
                    connection.message_log.clear()
                    for _this_connection_message_id in _message_references:
                        original_message_id = _message_references[_this_connection_message_id]
                        message_package = self.message_packages[original_message_id]
                        connection.message_log[int(_this_connection_message_id)] = message_package

                    # Add it to master servers
                    self.connections[_channel_id] = connection
                    self.active_connections.append(_channel_id)

        print("Finished Loading For " + self.name)

    async def annex(self, interaction: discord.Interaction, level: int):
        """
        Return if already annexed.
        Annex with pre-existing data or do a fresh annex.
        """
        annexed = False
        for channel in self.active_connections:
            if channel == interaction.channel_id:
                annexed = True
                break

        if not annexed:
            if FM.file_exists(self.name, interaction.channel_id):
                _server_data_dict = FM.retrieve_connection_data(self.name, interaction.channel_id)
                _server_id = _server_data_dict[FM.CONNECTION.SERVER_ID]
                _webhook_id = _server_data_dict[FM.CONNECTION.WEBHOOK_ID]
                _channel_id = _server_data_dict[FM.CONNECTION.CHANNEL_ID]
                _server_acronym = _server_data_dict[FM.CONNECTION.SERVER_ACRONYM]
                _level = _server_data_dict[FM.CONNECTION.LEVEL]
                _message_references = _server_data_dict[FM.CONNECTION.MESSAGE_REFERENCES]

                chosen_channel = MNG.Manager.client.get_channel(interaction.channel_id)
                chosen_webhook = None

                # Prioritize finding exact webhook first
                webhooks = await chosen_channel.webhooks()

                for webhook in webhooks:
                    if webhook.name == MNG.Manager.OFFICIAL_WEBHOOK_NAME and webhook.id == _webhook_id:
                        chosen_webhook = webhook

                for webhook in webhooks:
                    if webhook.name == MNG.Manager.OFFICIAL_WEBHOOK_NAME:
                        chosen_webhook = webhook

                if chosen_webhook is None:
                    try:
                        chosen_webhook = await chosen_channel.create_webhook(name=MNG.Manager.OFFICIAL_WEBHOOK_NAME)
                    except discord.HTTPException as e:
                        if e.status >= 400 < 500:
                            await ult.print_failure(chosen_channel, "Unable To Annex. Try Again")
                            return
                        elif e.status >= 500 < 600:
                            print("Server is not available at 'annex()'")
                            return
                    except discord.DiscordException as e:
                        logging.log(1, e)
                        return

                # Instantiate Server Object
                connection = Connection.Connection(_server_id, chosen_webhook, chosen_channel, _server_acronym, _level)

                # Add Message Packages
                connection.message_log.clear()
                for this_connection_message_id in _message_references:
                    original_message_id = _message_references[this_connection_message_id]
                    message_package = self.message_packages[original_message_id]
                    connection.message_log[this_connection_message_id] = message_package

                # Add it to master servers
                self.connections[_channel_id] = connection
                self.active_connections.append(_channel_id)

            elif not FM.file_exists(self.name, interaction.channel_id):
                # Create acronym from server name
                server_name = interaction.guild.name
                server_name = server_name.strip(" ")
                server_acronym = ""

                while server_name.find(" ") != -1:
                    index = server_name.index(" ") + 1
                    server_acronym += server_name[0]
                    server_name = server_name[index:]
                    server_name = server_name.strip(" ")
                server_acronym += server_name[0]
                server_acronym = server_acronym.upper()

                # get channel
                chosen_channel = interaction.channel

                # Get webhook
                chosen_webhook = None
                for webhook in await chosen_channel.webhooks():
                    if webhook.name == MNG.Manager.OFFICIAL_WEBHOOK_NAME:
                        try:
                            await webhook.delete()
                            chosen_webhook = await chosen_channel.create_webhook(name=MNG.Manager.OFFICIAL_WEBHOOK_NAME)
                        except discord.HTTPException as e:
                            if e.status >= 400 < 500:
                                await ult.print_failure(chosen_channel, "Unable To Annex. Try Again")
                                return
                            elif e.status >= 500 < 600:
                                print("Server is not available at 'annex()'")
                                return
                        except discord.DiscordException as e:
                            logging.log(1, e)
                            return

                if chosen_webhook is None:
                    try:
                        chosen_webhook = await chosen_channel.create_webhook(name=MNG.Manager.OFFICIAL_WEBHOOK_NAME)
                    except discord.HTTPException as e:
                        if e.status >= 400 < 500:
                            await ult.print_failure(chosen_channel, "Unable To Annex. Try Again")
                            return
                        elif e.status >= 500 < 600:
                            print("Server is not available at 'annex()'")
                            return
                    except discord.DiscordException as e:
                        logging.log(1, e)
                        return

                # create server object
                connection = Connection.Connection(interaction.guild_id, chosen_webhook, chosen_channel, server_acronym, level)

                # Add to list of participating server and server object
                self.connections[chosen_channel.id] = connection
                self.active_connections.append(chosen_channel.id)

                # create a file for this server
                FM.save_connection_data(self.name, connection)
                FM.save_network_list(self)
                FM.save_network_packages(self)

    async def nannex(self, interaction: discord.Interaction):
        self.connections.pop(interaction.channel_id)
        self.active_connections.remove(interaction.channel_id)
        await ult.print_success(interaction.channel, "Successfully Removed")

    async def erase(self, interaction: discord.Interaction):
        for file in FM.get_json_connection_files(self):
            connection = int(file)
            if connection == interaction.channel_id:
                for active_connection in self.active_connections:
                    if active_connection == connection:
                        raise ConnectyException.ConnectionIsActive("Can't on an active channel")
                FM.delete_connection_data(self, file)
            else:
                continue

    async def sync(self, interaction: discord.Interaction, new_channel_id: int):
        new_channel = await interaction.guild.fetch_channel(new_channel_id)
        try:
            connection = self.connections[interaction.channel_id]
        except KeyError:
            raise ConnectyException.UnknownIdentification("Irrelevant Channel")

        try:
            await connection.webhook.edit(reason="Webhook Channel Output Changed", channel=new_channel)
        except discord.HTTPException:
            return
        except Exception as e:
            print(str(e))

    async def delete(self, interaction: discord.Interaction, target_message_id: int):
        # Get Message Package
        try:
            this_connection = self.connections[interaction.channel_id]
        except KeyError:
            raise ConnectyException.UnknownIdentification("Irrelevant Channel")
        try:
            target_message_package = this_connection.message_log[target_message_id]
        except KeyError:
            raise ConnectyException.UnknownIdentification("Unknown Message ID")

        # Delete original message
        original_singular_message = target_message_package.original_singular_message
        try:
            original_connection = self.connections[original_singular_message.channel_id]
        except KeyError:
            raise ConnectyException.UnknownIdentification("Connection Not Available")

        # Admin cannot delete message from a higher server
        if this_connection.level < original_connection.level:
            raise ConnectyException.ConnectyActionFailed("Insufficient Permission")

        # Delete Original Message
        try:
            await original_connection.delete_message(original_singular_message.message_id)
        except ConnectyException.NotFound:
            pass
        except ConnectyException.DiscordActionFailed:
            pass

        # Delete all relayed messages
        relayed_singular_messages = target_message_package.relayed_singular_messages
        for relayed_singular_message in relayed_singular_messages:
            try:
                relayed_connection = self.connections[relayed_singular_message.channel_id]
            except KeyError:
                continue

            try:
                await relayed_connection.delete_message(relayed_singular_message.message_id)
            except ConnectyException.NotFound:
                continue
            except ConnectyException.DiscordActionFailed:
                continue

        # Mark as deleted to all replied messages
        if len(target_message_package.volunteer_message_packages) != 0:
            for replied_message_package in target_message_package.volunteer_message_packages:
                replied_singular_messages = replied_message_package.relayed_singular_messages
                for replied_singular_message in replied_singular_messages:
                    try:
                        other_connection = self.connections[replied_singular_message.channel_id]
                    except KeyError:
                        continue
                    try:
                        await other_connection.edit_reply_deleted(replied_singular_message.message_id)
                    except ConnectyException.NotFound:
                        continue
                    except ConnectyException.DiscordActionFailed:
                        continue
