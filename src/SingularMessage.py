import FileManager as FM

class SingularMessage:

    def __init__(self, channel_id: int, message_id: int, jump_url: str):
        self.channel_id = channel_id
        self.message_id = message_id
        self.jump_url = jump_url

    def create_dict(self):
        return {
            FM.SINGULAR_MESSAGE.CHANNEL_ID: self.channel_id,
            FM.SINGULAR_MESSAGE.MESSAGE_ID: self.message_id,
            FM.SINGULAR_MESSAGE.JUMP_URL: self.jump_url
        }