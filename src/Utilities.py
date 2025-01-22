import discord
import logging
import Manager as MNG

def is_power_user(message: discord.Message):
    return message.author.id == 1101153872870899712

def is_mod_user(message: discord.Message):
    if message.author.id == 1101153872870899712:
        return True
    elif message.author.id == message.guild.owner_id:
        return True
    else:
        return message.author.guild_permissions.administrator

async def print_failure(channel: discord.TextChannel, text: str):
    try:
        await channel.send(content=text)
    except discord.DiscordException as e:
        logging.log(2, e)
        return


async def print_success(channel: discord.TextChannel, text: str):
    try:
        await channel.send(content=text)
    except discord.DiscordException as e:
        logging.log(2, e)
        return

def generate_code():

    code = MNG.Manager.counter
    MNG.Manager.counter += 1
    return code

def remove_pings(content: str, channel: discord.TextChannel):
    searching_index = 0
    while searching_index < len(content):
        if content.find("<", searching_index) != -1:
            lt_index = content.find("<", searching_index)
            if content[lt_index + 1] == "@":
                searching_index = lt_index + 2
                possible_number = content[searching_index]
                user_id = str()
                while possible_number.isdigit():
                    user_id += content[searching_index]
                    searching_index += 1
                    possible_number = content[searching_index]

                if possible_number == ">":
                    user_id = int(user_id)
                    member = channel.guild.get_member(user_id)
                    if member != None:
                        content = content.replace("<@{0}>".format(str(user_id)), "#{0}".format(member.display_name))
                        searching_index =+ 1
                    else:
                        content = content.replace("<@{0}>".format(str(user_id)), "#{0}".format("unknown"))
                        searching_index = + 1
                else:
                    searching_index += 1
            else:
                searching_index = lt_index + 1
        else:
            break

    # REMOVE EVERYONE AND HERE PING
    if content.find("@everyone") != -1 or content.find("@here") != -1:
        return "|BLOCKED|"

    return content

async def send_response(interaction: discord.Interaction, text: str):
    # noinspection PyUnresolvedReferences
    await interaction.response.send_message(text, ephemeral=True)

def auto_strip(maximum: int, text: str):
    if len(text) > maximum:
        shortened_text = text[:maximum - 3]
        return shortened_text + "..."
    else:
        return text
