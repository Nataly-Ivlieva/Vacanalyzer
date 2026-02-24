from peewee import ForeignKeyField, CharField, FloatField 
from models.BaseModel import BaseModel
from models.Job import Job
from models.Location import Location

class JobLocation(BaseModel):
    job = ForeignKeyField(Job, backref="locations")
    location = ForeignKeyField(Location, backref="jobs")
    district = CharField(null=True)   
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
