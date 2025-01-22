import logging
import Reply
import discord
import SingularMessage as SM
import MessagePackage as MP
import ConnectyException
import Network
import Connection
from Manager import Manager as MNG

async def handle_regular_message(message: discord.Message, network: Network.Network):
    # CHECK 1: IGNORE DMS
    if message.guild.id is None:
        return

    # CHECK 2: IGNORE IF NOT ANNEXED
    is_annexed = False
    for active_connection in network.active_connections:
        if message.channel.id == active_connection:
            is_annexed = True
            break
    if not is_annexed:
        print("not annexed")
        return

    # CHECK 7: IGNORE BANNED
    for ban_code in MNG.banned:
        banned_user = MNG.banned[ban_code]
        if message.author.id == banned_user.user_id:
            await message.delete()
            return
    try:
        this_connection = network.connections[message.channel.id]
    except KeyError:
        return

    # CHECK 4: IGNORE CONNECTY MESSAGES
    if this_connection.webhook.id == message.author.id:
        return

    # CHECK 6: IGNORE THE BOT ITSELF
    if message.author.id == MNG.client.user.id:
        return

    # Initiate packing
    original_singular_message = SM.SingularMessage(this_connection.channel.id, message.id, message.jump_url)
    relayed_singular_messages = list()
    message_package = MP.MessagePackage(original_singular_message, relayed_singular_messages)

    # Relay the message to all servers
    for channel_id in network.connections:
        other_connection = network.connections[channel_id]

        if other_connection.channel.id == this_connection.channel.id:
            # Points to an empty message package yet to be filled
            this_connection.message_log[original_singular_message.message_id] = message_package
        else:
            try:
                relayed_singular_message = await other_connection.send_message(message, this_connection)
            except ConnectyException.DiscordActionFailed:
                continue
            relayed_singular_messages.append(relayed_singular_message)

            # Points to an empty message package yet to be filled
            other_connection.message_log[relayed_singular_message.message_id] = message_package

    # Add it into the master message package dict
    network.message_packages[original_singular_message.message_id] = message_package
    return

async def handle_reply_message(message: discord.Message, network: Network.Network):
    print("BOT ID " + str(MNG.client.user.id))
    # CHECK 1: IGNORE DMS
    if message.guild.id is None:
        return

    # CHECK 2: IGNORE IF NOT ANNEXED
    is_annexed = False
    for active_connection in network.active_connections:
        if message.channel.id == active_connection:
            is_annexed = True
            break
    if not is_annexed:
        return

    # CHECK 7: IGNORE BANNED
    for ban_code in MNG.banned:
        banned_user = MNG.banned[ban_code]
        if message.author.id == banned_user.user_id:
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            return
    try:
        this_connection = network.connections[message.channel.id]
    except KeyError:
        return

    # CHECK 4: IGNORE CONNECTY MESSAGES
    if this_connection.webhook.id == message.author.id:
        return

    # CHECK 6: IGNORE THE BOT ITSELF
    if message.author.id == MNG.client.user.id:
        return

    # Obtain the reference message
    is_reference_available = True
    reference_id = message.reference.message_id
    reference_message = None

    try:
        reference_message_package = this_connection.message_log[reference_id]
        reference_singular_message = reference_message_package.original_singular_message
        reference_connection = network.connections[reference_singular_message.channel_id]
        reference_message_id = reference_singular_message.message_id
        reference_message = await reference_connection.channel.fetch_message(reference_message_id)
    except KeyError:
        reference_message = await this_connection.channel.fetch_message(reference_id)
        reference_singular_message = SM.SingularMessage(this_connection.channel.id,
                                                        reference_id,
                                                        reference_message.jump_url)
        reference_message_package = MP.MessagePackage(reference_singular_message, [])
        reference_connection = this_connection
        this_connection.message_log[reference_id] = reference_message_package
    except discord.NotFound:
        is_reference_available = False
    except discord.HTTPException:
        is_reference_available = False
    except discord.DiscordException as e:
        logging.log(1, e)

    if is_reference_available and reference_message is not None:

        # The username of whomever the reference was
        reference_username = reference_message.author.display_name
        if reference_username.find("|") != -1:
            index_position = reference_username.index("|") + 2
            reference_username = reference_username[index_position:]
        reference_username = "{0} | {1}".format(reference_connection.server_acronym.upper(), reference_username)

        # The person that volunteered to reply
        volunteer_username = message.author.display_name
        if volunteer_username.find("|") != -1:
            index_position = volunteer_username.index("|") + 2
            volunteer_username = volunteer_username[index_position:]
        volunteer_username = "{0} | {1}".format(this_connection.server_acronym.upper(), volunteer_username)

        reply = Reply.Reply(
            volunteer_username,
            message,
            reference_username,
            reference_message,
            reference_message_package)

        # Initiate Volunteer Packaging
        volunteer_message = SM.SingularMessage(this_connection.channel.id, message.id, message.jump_url)
        volunteer_message_package = MP.MessagePackage(volunteer_message, [])
        this_connection.message_log[volunteer_message.message_id] = volunteer_message_package

        # Relay the replies to every other server except this one
        for channel_id in network.connections:
            other_connection = network.connections[channel_id]

            if other_connection.channel.id != this_connection.channel.id:
                # Relay the reply and store it into the volunteer package
                try:
                    relayed_singular_message = await other_connection.send_reply(reply)
                except ConnectyException.DiscordActionFailed:
                    continue

                # If nothing is returned
                if relayed_singular_message is None:
                    this_connection.message_log.pop(volunteer_message.message_id)
                    this_connection.message_log.pop(reference_id)
                    return

                volunteer_message_package.relayed_singular_messages.append(relayed_singular_message)

                # Have the other server's server log reference this volunteer package by its relayed reply message id
                other_connection.message_log[relayed_singular_message.message_id] = volunteer_message_package

        # Have volunteer package marked as a reply to the reference package
        reference_message_package.volunteer_message_packages.append(volunteer_message_package)

        # add message packages to master message package dict
        network.message_packages[reference_id] = reference_message_package
        network.message_packages[message.id] = volunteer_message_package
        return

async def handle_message_edit(previous_message: discord.Message, new_message: discord.Message, network: Network.Network):
    # CHECK 1: IGNORE DMS
    if previous_message.guild is None:
        return

    # CHECK 2: IGNORE IF NOT ANNEXED
    is_annexed = False
    for active_connection in network.active_connections:
        if previous_message.channel.id == active_connection:
            is_annexed = True
            break
    if not is_annexed:
        return

    # CHECK 3: IGNORE IRRELEVANT CHANNELS
    try:
        this_connection = network.connections[previous_message.channel.id]
    except KeyError:
        return

    # CHECK 4: IGNORE CONNECTY MESSAGES
    if this_connection.webhook.id == previous_message.author.id:
        return

    # Ignore messages that are not logged
    try:
        target_message_package = this_connection.message_log[previous_message.id]
    except KeyError:
        return

    # Edit relayed messages
    relayed_singular_messages = target_message_package.relayed_singular_messages
    for relayed_singular_message in relayed_singular_messages:
        try:
            other_connection = network.connections[relayed_singular_message.channel_id]
            await other_connection.edit_message(new_message, relayed_singular_message.message_id)
        except KeyError:
            continue
        except ConnectyException.NotFound:
            continue
        except ConnectyException.DiscordActionFailed:
            continue

    # Edit messages in replied to relay messages
    for replied_message_package in target_message_package.volunteer_message_packages:
        replied_singular_messages = replied_message_package.relayed_singular_messages
        for replied_singular_message in replied_singular_messages:
            try:
                other_connection = network.connections[replied_singular_message.channel_id]
                await other_connection.edit_reply(new_message, replied_singular_message.message_id)
            except KeyError:
                continue
            except ConnectyException.NotFound:
                continue
            except ConnectyException.DiscordActionFailed:
                continue

async def handle_raw_message_edit(raw_message_update_event: discord.RawMessageUpdateEvent, network: Network.Network):
    # CHECK 1: IGNORE DMS
    if raw_message_update_event.guild_id is None:
        return

    # CHECK 2: IGNORE IF NOT ANNEXED
    is_annexed = False
    for active_connection in network.active_connections:
        if raw_message_update_event.channel_id == active_connection:
            is_annexed = True
            break
    if not is_annexed:
        return

    # CHECK 3: IGNORE IRRELEVANT CHANNELS
    try:
        this_connection = network.connections[raw_message_update_event.channel_id]
    except KeyError:
        return

    # Fetch Message
    try:
        message = await (MNG.client.get_guild(raw_message_update_event.guild_id).
                         get_channel(raw_message_update_event.channel_id).
                         fetch_message(raw_message_update_event.message_id))
    except discord.HTTPException:
        return

    # CHECK 4: IGNORE CONNECTY MESSAGES
    if this_connection.webhook.id == message.author.id:
        return

    # Ignore messages that are not logged
    try:
        target_message_package = this_connection.message_log[message.id]
    except KeyError:
        return

    # Edit relayed messages
    relayed_singular_messages = target_message_package.relayed_singular_messages
    for relayed_singular_message in relayed_singular_messages:
        try:
            other_connection = network.connections[relayed_singular_message.channel_id]
        except KeyError:
            continue
        try:
            await other_connection.edit_message(message, relayed_singular_message.message_id)
        except ConnectyException.NotFound:
            continue
        except ConnectyException.DiscordActionFailed:
            continue

    # Edit messages in replied to relay messages
    for replied_message_package in target_message_package.volunteer_message_packages:
        replied_singular_messages = replied_message_package.relayed_singular_messages
        for replied_singular_message in replied_singular_messages:
            try:
                other_connection = network.connections[replied_singular_message.channel_id]
                await other_connection.edit_reply(message, replied_singular_message.message_id)
            except KeyError:
                continue
            except ConnectyException.NotFound:
                continue
            except ConnectyException.DiscordActionFailed:
                continue

async def handle_message_delete(message: discord.Message, network: Network.Network):
    # CHECK 1: IGNORE DMS
    if message.guild is None:
        return

    # CHECK 2: IGNORE IF NOT ANNEXED
    is_annexed = False
    for active_connection in network.active_connections:
        if message.channel.id == active_connection:
            is_annexed = True
            break
    if not is_annexed:
        return

    # CHECK 3: IGNORE IRRELEVANT CHANNELS
    try:
        this_connection = network.connections[message.channel.id]
    except KeyError:
        return

    # CHECK 4: IGNORE CONNECTY MESSAGES
    if this_connection.webhook.id == message.author.id:
        return

    await user_delete_message(this_connection, message.id, network)

async def handle_raw_message_delete(raw_message_delete_event: discord.RawMessageDeleteEvent, network: Network.Network):
    # CHECK 1: IGNORE DMS
    if raw_message_delete_event.guild_id is None:
        return

    # CHECK 2: IGNORE IF NOT ANNEXED
    is_annexed = False
    for active_connection in network.active_connections:
        if raw_message_delete_event.channel_id == active_connection:
            is_annexed = True
            break
    if not is_annexed:
        return

    # CHECK 3: IGNORE IRRELEVANT CHANNELS
    try:
        this_connection = network.connections[raw_message_delete_event.channel_id]
    except KeyError:
        return

    # CHECK 9: Make sure ID was an original ID
    is_original = False
    for original_singular_message_id in network.message_packages:
        if original_singular_message_id == raw_message_delete_event.message_id:
            is_original = True
    if not is_original:
        return

    await user_delete_message(this_connection, raw_message_delete_event.message_id, network)

async def user_delete_message(this_connection: Connection.Connection, message_id: int, network: Network.Network):
    # Get Message Package
    target_message_package = this_connection.message_log[message_id]

    # Delete all relayed messages
    relayed_singular_messages = target_message_package.relayed_singular_messages
    for relayed_singular_message in relayed_singular_messages:
        try:
            relayed_connection = network.connections[relayed_singular_message.channel_id]
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
                    other_connection = network.connections[replied_singular_message.channel_id]
                except KeyError:
                    continue
                try:
                    await other_connection.edit_reply_deleted(replied_singular_message.message_id)
                except ConnectyException.NotFound:
                    continue
                except ConnectyException.DiscordActionFailed:
                    continue
