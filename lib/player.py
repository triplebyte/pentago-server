class Player(object):
    def __init__(self, name, connection):
        self.name = name 
        self.connection = connection
    
    def send_message(self, message):
        self.connection.transport.write('\n'.join(message) + '\n\n')