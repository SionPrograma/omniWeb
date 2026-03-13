import logging
import secrets
from typing import Dict, Any, Optional
from .models import UserIdentity

logger = logging.getLogger(__name__)

class OAuthProvider:
    def __init__(self, name: str, client_id: str, client_secret: str, auth_url: str, token_url: str, user_info_url: str):
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.user_info_url = user_info_url

    def get_login_url(self, redirect_uri: str, state: str) -> str:
        return f"{self.auth_url}?client_id={self.client_id}&redirect_uri={redirect_uri}&response_type=code&state={state}&scope=openid email profile"

class OAuthManager:
    def __init__(self):
        self.providers: Dict[str, OAuthProvider] = {}
        self._states: Dict[str, str] = {} # state -> provider_name

    def register_provider(self, provider: OAuthProvider):
        self.providers[provider.name] = provider
        logger.info(f"Registered OAuth Provider: {provider.name}")

    def generate_state(self, provider_name: str) -> str:
        state = secrets.token_urlsafe(16)
        self._states[state] = provider_name
        return state

    def verify_state(self, state: str) -> Optional[str]:
        return self._states.pop(state, None)

    async def handle_callback(self, provider_name: str, code: str, redirect_uri: str) -> UserIdentity:
        """
        In a real implementation, this would:
        1. Exchange code for token via token_url
        2. Fetch user info via user_info_url
        3. Parse user info into UserIdentity
        
        For v1 Identity Layer, we provide a robust mock flow that validates the provider.
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
            
        logger.info(f"Processing OAuth callback for {provider_name}")
        
        # MOCK FLOW (Phase 15 Template)
        # In production, replace with actual httpx/requests calls to provider endpoints.
        
        mock_data = {
            "google": {"id": "g123", "name": "Google User", "email": "user@google.com", "avatar": "https://google.com/avatar.png"},
            "github": {"id": "gh456", "name": "GitHub Dev", "email": "dev@github.com", "avatar": "https://github.com/avatar.png"},
            "discord": {"id": "d789", "name": "Gamer", "email": "pro@discord.com", "avatar": "https://discord.com/avatar.png"},
            "facebook": {"id": "fb000", "name": "FB Friend", "email": "me@fb.com", "avatar": ""},
            "apple": {"id": "ap999", "name": "Apple Fan", "email": "icloud@apple.com", "avatar": ""},
            "reddit": {"id": "rd111", "name": "Redditor", "email": "user@reddit.com", "avatar": ""},
            "twitch": {"id": "tw222", "name": "Streamer", "email": "live@twitch.tv", "avatar": ""}
        }
        
        user_info = mock_data.get(provider_name, {"id": "unknown", "name": "Unknown", "email": None, "avatar": None})
        
        return UserIdentity(
            user_id=user_info["id"],
            provider=provider_name,
            display_name=user_info["name"],
            email=user_info["email"],
            avatar=user_info["avatar"]
        )

oauth_manager = OAuthManager()

# Setup default placeholder providers (to be configured via env)
from backend.core.config import settings

# This list matches the Phase 15 requirements
for p_name in ["google", "facebook", "apple", "github", "discord", "reddit", "twitch"]:
    oauth_manager.register_provider(OAuthProvider(
        name=p_name,
        client_id=getattr(settings, f"{p_name.upper()}_CLIENT_ID", "mock_id"),
        client_secret=getattr(settings, f"{p_name.upper()}_CLIENT_SECRET", "mock_secret"),
        auth_url=f"https://{p_name}.com/auth",
        token_url=f"https://{p_name}.com/token",
        user_info_url=f"https://{p_name}.com/userinfo"
    ))
