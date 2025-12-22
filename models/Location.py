from peewee import CharField
from models.BaseModel import BaseModel

class Location(BaseModel):
    display_name = CharField(unique=True)