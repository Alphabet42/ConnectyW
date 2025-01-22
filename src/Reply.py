import discord

import MessagePackage

class Reply:

    def __init__(self, volunteer_username: str, volunteer_message: discord.Message, reference_username: str, reference_message: discord.Message, reference_message_package: MessagePackage.MessagePackage):
        self.volunteer_username = volunteer_username
        self.volunteer_message = volunteer_message
        self.reference_username = reference_username
        self.reference_message = reference_message
        self.reference_message_package = reference_message_package