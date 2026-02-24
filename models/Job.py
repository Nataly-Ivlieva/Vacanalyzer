from peewee import CharField, TextField, BooleanField, ForeignKeyField, DateField
from models.BaseModel import BaseModel
from models.Tech import Tech

class Job(BaseModel):
    job_id = CharField(unique=True)
    title = CharField()
    description = TextField()
    salary_is_predicted = BooleanField()
    redirect_url = TextField()
    company = CharField()
    tech = ForeignKeyField(Tech, backref="jobs")
    date = DateField(null=True)
