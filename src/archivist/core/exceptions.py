import uuid
class TimeoutError(Exception):
    def __init__(self, msg) -> None:
        super().__init__(msg)
        
class ArchivistError(Exception):
    pass

class MessageUUIDError(ArchivistError):
    def __init__(self, msg, uuid:uuid.UUID,  conv_id):
        super().__init__(msg)
        self.uuid = uuid
        self.conv_id = conv_id

class EmptyConversationError(ArchivistError):
    def __init__(self, msg, conv_id):
        super().__init__(msg)
        self.conv_id = conv_id