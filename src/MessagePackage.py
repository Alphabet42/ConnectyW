import FileManager as FM

class MessagePackage:

    def __init__(self, original_singular_message, relayed_singular_messages: list):
        self.original_singular_message = original_singular_message
        self.relayed_singular_messages = relayed_singular_messages
        self.volunteer_message_packages = list()

    def create_dict(self):
        message_package_dict = dict()

        # Save Original Message
        message_package_dict[FM.MESSAGE_PACKAGE.ORIGINAL_SINGULAR_MESSAGE] = self.original_singular_message.create_dict()

        # Save Relayed Messages
        relayed_singular_messages_list = list()
        for relayed_singular_message in self.relayed_singular_messages:
            relayed_singular_messages_list.append(relayed_singular_message.create_dict())
        message_package_dict[FM.MESSAGE_PACKAGE.RELAYED_SINGULAR_MESSAGES] = relayed_singular_messages_list

        # Save the volunteer packages
        volunteer_original_message_ids_list = list()
        for volunteer_message_package in self.volunteer_message_packages:
            original_singular_message_id = volunteer_message_package.original_singular_message.message_id
            volunteer_original_message_ids_list.append(original_singular_message_id)

        message_package_dict[FM.MESSAGE_PACKAGE.VOLUNTEER_ORIGINAL_MESSAGE_IDS] = volunteer_original_message_ids_list

        return message_package_dict
