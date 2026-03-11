from .user import User


class UserDataModelHandler:
    @classmethod
    def user_query(cls, user_id: str) -> dict:
        return {"account.user_id": user_id}

    @classmethod
    async def find_by_user_id(cls, user_id: str) -> User | None:
        return await cls.find_one(cls.user_query(user_id))

    @classmethod
    async def add_saved_recipe(cls, user_id: str, recipe_id: str) -> None:
        await cls.update_one(
            cls.user_query(user_id),
            {"$addToSet": {"interactions.saved_recipe_ids": recipe_id}},
        )

    @staticmethod
    def _preview_user(
        user_id: str,
        name: str,
        email: str,
        priority: str = "Improving Health",
    ) -> User:
        return User(
            account=User.Account(user_id=user_id, email=email),
            profile=User.Profile(name=name, goals=[priority]),
            interactions=User.Interactions(),
        )

    SEED_DATA = [
        _preview_user(
            "preview-user-alice",
            "Alice",
            "alice@test.sprout.com",
        ),
        _preview_user(
            "preview-user-bob",
            "Bob",
            "bob@test.sprout.com",
        ),
        _preview_user(
            "preview-user-free",
            "Free User",
            "free@test.sprout.com",
        ),
    ]
