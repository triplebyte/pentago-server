from twisted.web.resource import Resource
from twisted.web.resource import NoResource


class RoomDisplay(Resource):
    isLeaf = True
    def __init__(self, room):
        self.room = room

    def render_GET(self, request):
        r = self.room.render()
        meta = "<meta http-equiv=\"refresh\" content=\"3\">"
        return "<html><head>%s<h1>Room %s</h1></head>%s</html>" % (meta, self.room.room_id, r)


class RoomList (Resource):
    def __init__(self, manager):
        self.children = []
        self.manager = manager

    def getChild(self, name, request):
        if name == '':
            return self
        if self.manager.rooms.get(name):
            return RoomDisplay(self.manager.rooms[name])
        else:
            return NoResource()

    def render_GET(self, request):
        games = "<ul>"
        if len(self.manager.rooms):
            for room in self.manager.rooms.values():
                games += "<li><a href='/rooms/%s'>%s</a> (%s players, %s)</li>" % (room.room_id, room.room_id, len(room.players), room.state)
            games += "</ul>"
        else:
            games = "<h2>No Games :(</h2>"
        return "<html><head><h1>Game Rooms</h1></head>%s</html>" % games

class PentagoHttp (Resource):
    def __init__(self, manager):
        self.children = []
        self.manager = manager

    def getChild(self, name, request):
        if name == '':
            return self
        elif name == 'rooms':
            return RoomList(self.manager)
        else:
            return NoResource()


    def render_GET(self, request):
        return "<html><h1>Triplebyte Pentago Server!</h1><p>Rooms are <a href='/rooms'>here</a></p></html>"

