from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from supertokens_python import InputAppInfo, SupertokensConfig, init
from supertokens_python.recipe import emailpassword, session, thirdparty
from supertokens_python.recipe.emailpassword.interfaces import (
    APIInterface as EPAPIInterface,
)
from supertokens_python.recipe.emailpassword.interfaces import (
    APIOptions as EPAPIOptions,
)
from supertokens_python.recipe.emailpassword.interfaces import (
    EmailAlreadyExistsError,
    SignUpPostNotAllowedResponse,
    SignUpPostOkResult,
)
from supertokens_python.recipe.emailpassword.types import FormField
from supertokens_python.recipe.emailpassword.utils import EmailPasswordOverrideConfig
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.thirdparty.interfaces import (
    APIInterface as TPAPIInterface,
)
from supertokens_python.recipe.thirdparty.interfaces import (
    APIOptions as TPAPIOptions,
)
from supertokens_python.recipe.thirdparty.interfaces import (
    SignInUpNotAllowed,
    SignInUpPostNoEmailGivenByProviderResponse,
    SignInUpPostOkResult,
)
from supertokens_python.recipe.thirdparty.provider import (
    Provider,
    ProviderClientConfig,
    ProviderConfig,
    ProviderInput,
    RedirectUriInfo,
)
from supertokens_python.recipe.thirdparty.utils import ThirdPartyOverrideConfig
from supertokens_python.types.response import GeneralErrorResponse

from api.config import settings
from api.database import AsyncSessionLocal
from api.models import User, UserAuthMethod


def _override_emailpassword_apis(original: EPAPIInterface) -> EPAPIInterface:
    original_sign_up_post = original.sign_up_post

    async def sign_up_post(
        form_fields: list[FormField],
        tenant_id: str,
        session: SessionContainer | None,
        should_try_linking_with_session_user: bool | None,
        api_options: EPAPIOptions,
        user_context: dict[str, Any],
    ) -> SignUpPostOkResult | EmailAlreadyExistsError | SignUpPostNotAllowedResponse | GeneralErrorResponse:
        result = await original_sign_up_post(
            form_fields=form_fields,
            tenant_id=tenant_id,
            session=session,
            should_try_linking_with_session_user=should_try_linking_with_session_user,
            api_options=api_options,
            user_context=user_context,
        )
        if isinstance(result, SignUpPostOkResult):
            display_name = next((f.value for f in form_fields if f.id == "display_name"), None)
            email = result.user.emails[0]
            async with AsyncSessionLocal() as db:
                user_stmt = pg_insert(User).values(email=email, display_name=display_name)
                await db.execute(user_stmt.on_conflict_do_nothing(index_elements=["email"]))
                user = (await db.execute(select(User).where(User.email == email))).scalar_one()
                auth_stmt = pg_insert(UserAuthMethod).values(
                    user_id=user.id,
                    provider="emailpassword",
                    supertokens_user_id=result.user.id,
                )
                await db.execute(auth_stmt.on_conflict_do_nothing(index_elements=["supertokens_user_id"]))
                await db.commit()
        return result

    original.sign_up_post = sign_up_post  # ty: ignore[invalid-assignment]
    return original


def _override_thirdparty_apis(original: TPAPIInterface) -> TPAPIInterface:
    original_sign_in_up_post = original.sign_in_up_post

    async def sign_in_up_post(
        provider: Provider,
        redirect_uri_info: RedirectUriInfo | None,
        oauth_tokens: dict[str, Any] | None,
        session: SessionContainer | None,
        should_try_linking_with_session_user: bool | None,
        tenant_id: str,
        api_options: TPAPIOptions,
        user_context: dict[str, Any],
    ) -> SignInUpPostOkResult | SignInUpPostNoEmailGivenByProviderResponse | SignInUpNotAllowed | GeneralErrorResponse:
        result = await original_sign_in_up_post(
            provider=provider,
            redirect_uri_info=redirect_uri_info,
            oauth_tokens=oauth_tokens,
            session=session,
            should_try_linking_with_session_user=should_try_linking_with_session_user,
            tenant_id=tenant_id,
            api_options=api_options,
            user_context=user_context,
        )
        if isinstance(result, SignInUpPostOkResult) and result.created_new_recipe_user:
            email = result.user.emails[0]
            async with AsyncSessionLocal() as db:
                user_stmt = pg_insert(User).values(email=email, display_name=None)
                await db.execute(user_stmt.on_conflict_do_nothing(index_elements=["email"]))
                user = (await db.execute(select(User).where(User.email == email))).scalar_one()
                auth_stmt = pg_insert(UserAuthMethod).values(
                    user_id=user.id,
                    provider=provider.id,
                    supertokens_user_id=result.user.id,
                )
                await db.execute(auth_stmt.on_conflict_do_nothing(index_elements=["supertokens_user_id"]))
                await db.commit()
        return result

    original.sign_in_up_post = sign_in_up_post  # ty: ignore[invalid-assignment]
    return original


def init_supertokens() -> None:
    init(
        app_info=InputAppInfo(
            app_name="Lorekeeper Platform",
            api_domain=settings.api_domain,
            website_domain=settings.website_domain,
            api_base_path="/auth",
            website_base_path="/login",
        ),
        supertokens_config=SupertokensConfig(
            connection_uri=settings.supertokens_connection_uri,
        ),
        framework="fastapi",
        recipe_list=[
            emailpassword.init(
                sign_up_feature=emailpassword.InputSignUpFeature(
                    form_fields=[
                        emailpassword.InputFormField(id="display_name"),
                    ]
                ),
                override=EmailPasswordOverrideConfig(
                    apis=_override_emailpassword_apis,
                ),
            ),
            thirdparty.init(
                sign_in_and_up_feature=thirdparty.SignInAndUpFeature(
                    providers=[
                        ProviderInput(
                            config=ProviderConfig(
                                third_party_id="google",
                                clients=[
                                    ProviderClientConfig(
                                        client_id=settings.google_client_id,
                                        client_secret=settings.google_client_secret,
                                    )
                                ],
                            )
                        ),
                        ProviderInput(
                            config=ProviderConfig(
                                third_party_id="discord",
                                clients=[
                                    ProviderClientConfig(
                                        client_id=settings.discord_client_id,
                                        client_secret=settings.discord_client_secret,
                                    )
                                ],
                            )
                        ),
                    ]
                ),
                override=ThirdPartyOverrideConfig(
                    apis=_override_thirdparty_apis,
                ),
            ),
            session.init(),
        ],
    )
