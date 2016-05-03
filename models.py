from mongoengine import Document, StringField, IntField, DateTimeField
from datetime import datetime


class Repo(Document):
    name = StringField()
    user = StringField()
    status = StringField()
    progress = IntField()
    started_at = DateTimeField()
    completed_at = DateTimeField()

    def json(self):
        try:
            started = datetime.strftime(self.started_at, "%d-%b-%Y %H:%m")
        except:
            started = ''
        try:
            completed = datetime.strftime(self.completed_at, "%d-%b-%Y %H:%m")
        except:
            completed = ''
        return {
            'name': self.name,
            'user': self.user,
            'status': self.status,
            'progress': self.progress,
            'started_at': started,
            'completed_at': completed,
        }
