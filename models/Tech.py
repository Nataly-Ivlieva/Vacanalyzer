from peewee import CharField
from models.BaseModel import BaseModel

class Tech(BaseModel):
    name = CharField(unique=True)
