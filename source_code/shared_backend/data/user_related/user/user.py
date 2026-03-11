from database_dimension import MongoDBBaseModel
from pydantic import BaseModel


class User(MongoDBBaseModel, database="sprout_data", collection="users"):
    class Account(BaseModel):
        user_id: str
        email: str

    class Profile(BaseModel):
        name: str
        goals: list[str]

    class Interactions(BaseModel):
        saved_recipe_ids: list[str] = []
        dismissed_recipe_ids: list[str] = []
        blocked_user_ids: list[str] = []

    account: Account
    profile: Profile
    interactions: Interactions
