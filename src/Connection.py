import discord
import ConnectyException
import Reply
import SingularMessage as SM
import FileManager as FM
from ReplyUI import ReplyUI as UI, remove_pings, break_links
from Utilities import auto_strip
class Connection:

    def __init__(self, server_id: int, webhook: discord.Webhook, channel: discord.TextChannel, server_acronym: str, level: int):
        self.server_id = server_id
        self.webhook = webhook
        self.channel = channel
        self.server_acronym = server_acronym
        self.message_log = {}
        self.level = level

    def create_dict(self):
        connection_data = dict()

        # Save basic data
        connection_data[FM.CONNECTION.SERVER_ID] = self.server_id
        connection_data[FM.CONNECTION.WEBHOOK_ID] = self.webhook.id
        connection_data[FM.CONNECTION.CHANNEL_ID] = self.channel.id
        connection_data[FM.CONNECTION.SERVER_ACRONYM] = self.server_acronym
        connection_data[FM.CONNECTION.LEVEL] = self.level

        # Save this channel's message ids together with the original message ids
        message_references = dict()
        for this_connection_message_id in self.message_log:
            message_package = self.message_log[this_connection_message_id]
            message_references[this_connection_message_id] = message_package.original_singular_message.message_id
        connection_data[FM.CONNECTION.MESSAGE_REFERENCES] = message_references

        return connection_data

    async def send_reply(self, reply: Reply.Reply):
        is_reference_known = reply.reference_message_package.original_singular_message.channel_id == self.channel.id
        for singular_message in reply.reference_message_package.relayed_singular_messages:
            if singular_message.channel_id == self.channel.id:
                is_reference_known = True

        is_content_empty = len(reply.reference_message.content) == 0
        is_source = reply.reference_message.channel.id == self.channel.id
        has_attachments = reply.reference_message.attachments is not None

        if is_source:
            identifier = "<@{0}>".format(reply.reference_message.author.id)
        else:
            identifier = reply.reference_username
            if reply.reference_username.find(UI.INFO_FILE) != -1:
                identifier = identifier.replace(UI.INFO_FILE, "File")
            if reply.reference_username.find(UI.INFO_DELETED) != -1:
                identifier = identifier.replace(UI.INFO_DELETED, "Message Deleted")
            if reply.reference_username.find(UI.INVISIBLE_SYMBOL) != -1:
                identifier = identifier.replace(UI.INVISIBLE_SYMBOL, UI.SPACE)
            if reply.reference_username.find("@everyone") != -1 or reply.reference_username.find("@here") != -1:
                identifier = UI.BLOCKED
            identifier = "__" + identifier + "__"

        if is_content_empty and has_attachments:
            info = UI.INFO_FILE
        else:
            # Check if it contains reply content
            if reply.reference_message.content.find(UI.REPLY_SYMBOL) == 0:
                next_line_index = reply.reference_message.content.find("\n")
                reply.reference_message.content = reply.reference_message.content[next_line_index + 2:]
            reply.reference_message.content = remove_pings(reply.reference_message.content, reply.reference_message.channel)
            reply.reference_message.content = break_links(reply.reference_message.content)
            info = auto_strip(UI.MAXIMUM_REPLY_SIZE - len(identifier), reply.reference_message.content)
            print("SEND REPLY>" + info)

        if is_reference_known:
            this_connection_jump_url = str()
            all_singular_messages = reply.reference_message_package.relayed_singular_messages.copy()
            origin_singular_message = reply.reference_message_package.original_singular_message
            all_singular_messages.append(origin_singular_message)

            for singular_message in all_singular_messages:
                if singular_message.channel_id == self.channel.id:
                    this_connection_jump_url = singular_message.jump_url
                    break

            content = UI.REPLY_FORMAT_JUMP_URL_N.format(identifier,
                                                        info,
                                                        this_connection_jump_url,
                                                        remove_pings(reply.volunteer_message.content,
                                                                     reply.reference_message.channel))
        elif not is_reference_known:
            content = UI.REPLY_RAW_FORMAT_NONE_N.format(identifier,
                                                        UI.INVISIBLE_SYMBOL,
                                                        info,
                                                        UI.INVISIBLE_SYMBOL,
                                                        remove_pings(reply.volunteer_message.content,
                                                                     reply.reference_message.channel))

        # Attach Files
        files = list()
        if reply.volunteer_message.attachments is not None:
            for attachment in reply.volunteer_message.attachments:
                try:
                    files.append(await attachment.to_file())
                except discord.HTTPException:
                    pass

        # Relay the replies
        try:
            relayed_message = await self.webhook.send(content=content,
                                                      username=reply.volunteer_username,
                                                      avatar_url=reply.volunteer_message.author.display_avatar.url,
                                                      files=files,
                                                      wait=True)
        except discord.HTTPException:
            raise ConnectyException.DiscordActionFailed

        # Get the relayed message ID
        relayed_message_jump_url = relayed_message.jump_url
        relayed_message_jump_url = relayed_message_jump_url.strip()
        while relayed_message_jump_url.find("/") != -1:
            index = relayed_message_jump_url.find("/")
            relayed_message_jump_url = relayed_message_jump_url[index + 1:]
        relayed_message_id = int(relayed_message_jump_url)

        return SM.SingularMessage(self.channel.id, relayed_message_id, relayed_message.jump_url)

    """
    Raises:
        ConnectyException.DiscordActionFailed
            - When a webhook action fails to go through
    """

    async def send_message(self, message: discord.Message, this_connection):
        # Replace or create any identifier for username
        username = message.author.display_name
        if username.find("|") != -1:
            index = username.index("|") + 2
            username = username[index:]
        username = "{0} | {1}".format(this_connection.server_acronym.upper(), username)

        # Add Files
        files = list()
        for attachment in message.attachments:
            try:
                files.append(await attachment.to_file())
            except discord.HTTPException:
                pass

        # Relay Message
        try:
            relayed_message = await self.webhook.send(content=remove_pings(message.content, this_connection.channel),
                                                      username=username,
                                                      avatar_url=message.author.display_avatar.url,
                                                      wait=True,
                                                      files=files)
        except discord.HTTPException:
            raise ConnectyException.DiscordActionFailed

        # Get the relayed message ID
        relayed_message_jump_url = relayed_message.jump_url
        relayed_message_jump_url = relayed_message_jump_url.strip()
        while relayed_message_jump_url.find("/") != -1:
            index = relayed_message_jump_url.find("/")
            relayed_message_jump_url = relayed_message_jump_url[index + 1:]
        relayed_message_id = int(relayed_message_jump_url)

        return SM.SingularMessage(self.channel.id, relayed_message_id, relayed_message.jump_url)

    """
    Raises:
        ConnectyException.DiscordActionFailed
            - When a webhook action fails to go through
    """

    async def edit_message(self, new_message: discord.Message, message_id: int):
        try:
            relayed_message = await self.webhook.fetch_message(message_id)

            if relayed_message.content.find(UI.REPLY_SYMBOL) == 0:
                without_symbol = relayed_message.content[len(UI.REPLY_SYMBOL):]
                next_line_index = without_symbol.find("\n")
                if next_line_index == -1:
                    without_symbol += "\n"
                    next_line_index = without_symbol.find("\n")

                # Attempt to find jump url [INFO]
                searching_index = 0
                found_jump_url = False
                while searching_index < len(without_symbol):
                    if without_symbol.find("(", searching_index) != -1:
                        parentheses_start_index = without_symbol.find("(", searching_index)
                    else:
                        break
                    if without_symbol.find(")", searching_index) != -1:
                        parentheses_end_index = without_symbol.find(")", parentheses_start_index)
                    else:
                        searching_index = parentheses_start_index + 1
                        continue

                    jump_url_section = without_symbol[parentheses_start_index: parentheses_end_index + 1]
                    if len(jump_url_section) > 32:
                        possible_jump_url = jump_url_section[1: len(jump_url_section) - 1]
                        if (parentheses_end_index < next_line_index
                                and possible_jump_url.find("(") == -1
                                and possible_jump_url.find(")") == -1
                                and possible_jump_url.find("[") == -1
                                and possible_jump_url.find("]") == -1):
                            info_start_index = without_symbol.rfind(" [", 0, parentheses_start_index) + 1
                            info_end_index = parentheses_end_index
                            found_jump_url = True
                            break

                    searching_index = parentheses_start_index + 1

                if not found_jump_url:
                    message_deleted_index = without_symbol.find(UI.INFO_DELETED)
                    file_index = without_symbol.find(UI.INFO_FILE)

                    if (message_deleted_index != -1 and file_index == -1) or (message_deleted_index < file_index):
                        info_start_index = without_symbol.find(UI.INFO_DELETED)
                        info_end_index = info_start_index + len(UI.INFO_DELETED) - 1
                    elif (file_index != -1 and message_deleted_index == -1) or (file_index < message_deleted_index):
                        info_start_index = without_symbol.find(UI.INFO_FILE)
                        info_end_index = info_start_index + len(UI.INFO_FILE) - 1
                    elif file_index == -1 and message_deleted_index == -1:
                        info_start_index = without_symbol.find(UI.INVISIBLE_SYMBOL)
                        info_end_index = without_symbol.find(UI.INVISIBLE_SYMBOL, info_start_index + 1)

                identifier = without_symbol[:info_start_index - 1]
                info = without_symbol[info_start_index:info_end_index + 1]

                if found_jump_url:
                    content = UI.REPLY_KNOWN_FORMAT_N.format(identifier,
                                                             info,
                                                             remove_pings(new_message.content, new_message.channel))
                elif not found_jump_url:
                    content = UI.REPLY_RAW_FORMAT_NONE_N.format(identifier,
                                                                UI.INVISIBLE_SYMBOL,
                                                                info,
                                                                UI.INVISIBLE_SYMBOL,
                                                                remove_pings(new_message.content, new_message.channel))
            else:
                content = remove_pings(new_message.content, new_message.channel)

            print("CON>" + content + "<CON")

            await relayed_message.edit(content=content)
        except discord.NotFound:
            raise ConnectyException.NotFound
        except discord.HTTPException:
            raise ConnectyException.DiscordActionFailed

    """
    Raises:
        ConnectyException.DiscordActionFailed
            - When a webhook action fails to go through
        ConnectyException.NotFound
            - When the target message id is nowhere to be found
    """

    async def edit_reply_deleted(self, message_id: int):
        # Get Embed
        try:
            replied_message = await self.webhook.fetch_message(message_id)
        except discord.NotFound:
            raise ConnectyException.NotFound

        without_symbol = replied_message.content[len(UI.REPLY_SYMBOL):]
        next_line_index = without_symbol.find("\n")
        if next_line_index == -1:
            without_symbol += "\n"
            next_line_index = without_symbol.find("\n")

        # Attempt to find jump url [INFO]
        searching_index = 0
        found_jump_url = False
        while searching_index < len(without_symbol):
            if without_symbol.find("(", searching_index) != -1:
                parentheses_start_index = without_symbol.find("(", searching_index)
            else:
                break
            if without_symbol.find(")", searching_index) != -1:
                parentheses_end_index = without_symbol.find(")", parentheses_start_index)
            else:
                searching_index = parentheses_start_index + 1
                continue

            jump_url_section = without_symbol[parentheses_start_index: parentheses_end_index + 1]
            if len(jump_url_section) > 32:
                possible_jump_url = jump_url_section[1: len(jump_url_section) - 1]
                if (parentheses_end_index < next_line_index
                        and possible_jump_url.find("(") == -1
                        and possible_jump_url.find(")") == -1
                        and possible_jump_url.find("[") == -1
                        and possible_jump_url.find("]") == -1):
                    info_start_index = without_symbol.rfind(" [", 0, parentheses_start_index) + 1
                    info_end_index = parentheses_end_index
                    found_jump_url = True
                    break

            searching_index = parentheses_start_index + 1

        if not found_jump_url:
            message_deleted_index = without_symbol.find(UI.INFO_DELETED)
            file_index = without_symbol.find(UI.INFO_FILE)

            if (message_deleted_index != -1 and file_index == -1) or (message_deleted_index < file_index):
                info_start_index = without_symbol.find(UI.INFO_DELETED)
                info_end_index = info_start_index + len(UI.INFO_DELETED) - 1
            elif (file_index != -1 and message_deleted_index == -1) or (file_index < message_deleted_index):
                info_start_index = without_symbol.find(UI.INFO_FILE)
                info_end_index = info_start_index + len(UI.INFO_FILE) - 1
            elif file_index == -1 and message_deleted_index == -1:
                info_start_index = without_symbol.find(UI.INVISIBLE_SYMBOL)
                info_end_index = without_symbol.find(UI.INVISIBLE_SYMBOL, info_start_index + 1)

        info = without_symbol[info_start_index: info_end_index + 1]
        if info == UI.INFO_DELETED:
            return

        identifier = without_symbol[:info_start_index - 1]
        volunteer_content = without_symbol[info_end_index + 1:]

        if found_jump_url:
            content = UI.REPLY_KNOWN_FORMAT.format(identifier,
                                                   UI.INFO_DELETED,
                                                   volunteer_content)
        elif not found_jump_url:
            content = UI.REPLY_RAW_FORMAT_NONE.format(identifier,
                                                      UI.INVISIBLE_SYMBOL,
                                                      UI.INFO_DELETED,
                                                      UI.INVISIBLE_SYMBOL,
                                                      volunteer_content)

        try:
            await replied_message.edit(content=content)
            if replied_message.attachments is not None:
                await replied_message.remove_attachments()
        except discord.HTTPException:
            raise ConnectyException.DiscordActionFailed

    """
    Raises:
        ConnectyException.DiscordActionFailed
            - When a webhook action fails to go through
        ConnectyException.NotFound
            - When the target message id is nowhere to be found
    """

    async def edit_reply(self, new_message: discord.Message, message_id: int):
        try:
            replied_message = await self.webhook.fetch_message(message_id)
        except discord.NotFound:
            raise ConnectyException.NotFound

        without_symbol = replied_message.content[len(UI.REPLY_SYMBOL):]
        next_line_index = without_symbol.find("\n")
        if next_line_index == -1:
            without_symbol += "\n"
            next_line_index = without_symbol.find("\n")

        # Attempt to find jump url [INFO]
        searching_index = 0
        found_jump_url = False
        while searching_index < len(without_symbol):
            if without_symbol.find("(", searching_index) != -1:
                parentheses_start_index = without_symbol.find("(", searching_index)
            else:
                break
            if without_symbol.find(")", searching_index) != -1:
                parentheses_end_index = without_symbol.find(")", parentheses_start_index)
            else:
                searching_index = parentheses_start_index + 1
                continue

            jump_url_section = without_symbol[parentheses_start_index: parentheses_end_index + 1]
            if len(jump_url_section) > 32:
                possible_jump_url = jump_url_section[1: len(jump_url_section) - 1]
                if (parentheses_end_index < next_line_index
                        and possible_jump_url.find("(") == -1
                        and possible_jump_url.find(")") == -1
                        and possible_jump_url.find("[") == -1
                        and possible_jump_url.find("]") == -1):

                    jump_url = possible_jump_url
                    info_start_index = without_symbol.rfind(" [", 0, parentheses_start_index) + 1
                    info_end_index = parentheses_end_index
                    found_jump_url = True
                    break

            searching_index = parentheses_start_index + 1

        if not found_jump_url:
            message_deleted_index = without_symbol.find(UI.INFO_DELETED)
            file_index = without_symbol.find(UI.INFO_FILE)

            if (message_deleted_index != -1 and file_index == -1) or (message_deleted_index < file_index):
                info_start_index = without_symbol.find(UI.INFO_DELETED)
                info_end_index = info_start_index + len(UI.INFO_DELETED) - 1
            elif (file_index != -1 and message_deleted_index == -1) or (file_index < message_deleted_index):
                info_start_index = without_symbol.find(UI.INFO_FILE)
                info_end_index = info_start_index + len(UI.INFO_FILE) - 1
            elif file_index == -1 and message_deleted_index == -1:
                info_start_index = without_symbol.find(UI.INVISIBLE_SYMBOL)
                info_end_index = without_symbol.find(UI.INVISIBLE_SYMBOL, info_start_index + 1)

        identifier = without_symbol[:info_start_index - 1]
        volunteer_content = without_symbol[info_end_index + 1:]

        if len(new_message.content) > 0:
            info = break_links(new_message.content)
            info = remove_pings(info, new_message.channel)
            info = auto_strip(UI.MAXIMUM_REPLY_SIZE - len(identifier), info)
        else:
            info = UI.INFO_FILE

        if found_jump_url:
            content = UI.REPLY_FORMAT_JUMP_URL.format(identifier, info, jump_url, volunteer_content)
        elif not found_jump_url:
            content = UI.REPLY_RAW_FORMAT_NONE.format(identifier,
                                                      UI.INVISIBLE_SYMBOL,
                                                      info,
                                                      UI.INVISIBLE_SYMBOL,
                                                      volunteer_content)

        try:
            await replied_message.edit(content=content)
        except discord.HTTPException:
            raise ConnectyException.DiscordActionFailed

    """
    Raises:
        ConnectyException.DiscordActionFailed
            - When a webhook action fails to go through
        ConnectyException.NotFound
            - When the target message id is nowhere to be found
    """

    async def delete_message(self, message_id: int):
        try:
            target_message = await self.channel.fetch_message(message_id)
            await target_message.delete()
        except discord.NotFound:
            raise ConnectyException.NotFound
        except discord.HTTPException:
            raise ConnectyException.DiscordActionFailed

    """
    Raises:
        ConnectyException.DiscordActionFailed
            - When a webhook action fails to go through
        ConnectyException.NotFound
            - When the target message id is nowhere to be found
    """