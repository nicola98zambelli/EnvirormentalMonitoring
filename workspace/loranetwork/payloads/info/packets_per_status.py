import json


class PacketsPerStatus:
    def __init__(self, ok=0):
        self.OK = ok

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
