import logging
import os
from collections.abc import Awaitable, Callable
from typing import ClassVar

import jwt
from fast_server import APIOperation
from fastapi import Body, HTTPException
from jwt import PyJWKClient

from shared_backend.data.user_related.user.user import User

logger = logging.getLogger(__name__)


class AuthenticateUser(APIOperation):
    METHOD = "POST"
    APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"
    VALID_AUDIENCES = [
        "com.ecstasy.sprout",
        os.environ.get("APPLE_WEB_SERVICES_ID", "com.sprout.website"),
    ]

    _post_signup_hooks: ClassVar[list[Callable[[str], Awaitable]]] = []

    @classmethod
    def register_post_signup_hook(cls, hook: Callable[[str], Awaitable]):
        cls._post_signup_hooks.append(hook)

    WEBSITE_AUDIENCE = os.environ.get("APPLE_WEB_SERVICES_ID", "com.sprout.website")

    @classmethod
    async def _verify_apple_token(
        cls, identity_token: str
    ) -> tuple[str, str | None, str | list[str]]:
        jwks_client = PyJWKClient(cls.APPLE_PUBLIC_KEYS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(identity_token)
        decoded = jwt.decode(
            identity_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=cls.VALID_AUDIENCES,
            issuer="https://appleid.apple.com",
        )
        return decoded["sub"], decoded.get("email"), decoded.get("aud")

    async def execute(
        self,
        identity_token: str = Body(),
        name: str | None = Body(None),
        goals: list[str] = Body([]),
    ) -> dict:
        try:
            user_id, email, aud = await self._verify_apple_token(identity_token)
        except Exception:
            raise HTTPException(
                status_code=401, detail="Invalid or expired Apple identity token."
            )

        existing_user = await User.find_one({"account.user_id": user_id})

        if not existing_user:
            aud_list = [aud] if isinstance(aud, str) else (aud or [])
            if self.WEBSITE_AUDIENCE in aud_list:
                raise HTTPException(
                    status_code=403,
                    detail="Please sign up through the Sprout app first.",
                )
            if not email or not name:
                raise HTTPException(
                    status_code=400,
                    detail="Email and name are required to create a new user.",
                )

        if existing_user:
            updates = {}
            if email and not existing_user.account.email:
                updates["account.email"] = email
            if name and existing_user.profile.name != name:
                updates["profile.name"] = name
            if updates:
                await User.update_one({"account.user_id": user_id}, {"$set": updates})

            return {
                "user_id": user_id,
                "is_new_user": False,
                "name": name or existing_user.profile.name,
                "email": email or existing_user.account.email,
            }

        new_user = User(
            id=user_id,
            account=User.Account(user_id=user_id, email=email),
            profile=User.Profile(name=name, goals=goals),
            settings=User.Settings(),
            interactions=User.Interactions(),
        )
        await new_user.save()

        for hook in self._post_signup_hooks:
            await hook(user_id)

        logger.info(f"New user created: {user_id}")
        return {"user_id": user_id, "is_new_user": True, "name": name}
