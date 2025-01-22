import FileManager as FM

class BannedUser:

    def __init__(self, server_name: str, server_username: str, user_id: int, server_level: int, ban_code: int):
        self.server_name = server_name
        self.server_username = server_username
        self.user_id = user_id
        self.server_level = server_level
        self.ban_code = ban_code

    def create_dict(self):
        return {
            FM.BAN.SERVER_NAME: self.server_name,
            FM.BAN.SERVER_USERNAME: self.server_username,
            FM.BAN.USER_ID: self.user_id,
            FM.BAN.SERVER_LEVEL: self.server_level,
            FM.BAN.BAN_CODE: self.ban_code
        }
