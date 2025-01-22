import discord

class ReplyUI:
    INFO_FILE = "FILE"
    INFO_DELETED = "*Message Deleted*"
    BLOCKED = "BLOCKED"
    #INVISIBLE_SYMBOL = "᲼"
    INVISIBLE_SYMBOL = "ˑ"
    SPACE = " "
    REPLY_SYMBOL = "> "
    REPLY_FORMAT_JUMP_URL_N = REPLY_SYMBOL + "{0} [{1}]({2})\n{3}"
    REPLY_FORMAT_JUMP_URL = REPLY_SYMBOL + "{0} [{1}]({2}){3}"
    REPLY_KNOWN_FORMAT_N = REPLY_SYMBOL + "{0} {1}\n{2}"
    REPLY_KNOWN_FORMAT = REPLY_SYMBOL + "{0} {1}{2}"
    REPLY_RAW_FORMAT_NONE_N = REPLY_SYMBOL + "{0} {1}{2}{3}\n{4}"
    REPLY_RAW_FORMAT_NONE = REPLY_SYMBOL + "{0} {1}{2}{3}{4}"
    MAXIMUM_REPLY_SIZE = 50

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
                        content = content[:len(content) - 2]
                        print("UI CON>" + content + "<UI OCN")
                        searching_index = + 1
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
        return "BLOCKED"

    return content

def break_links(content: str):
    if content.find("https://") != -1:
        return content.replace("https://", "")
    elif content.find("http://") != -1:
        return content.replace("http://", "")
    else:
        return content