class InvalidPacketException(Exception):
    def __init__(self, message="Wrong packet"):
        self.message = message
        super().__init__(self.message)