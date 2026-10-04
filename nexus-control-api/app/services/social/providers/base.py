from abc import ABC, abstractmethod


class SocialProvider(ABC):
    platform_id = None
    usa_pkce = False

    @abstractmethod
    def build_authorize_url(self, state, redirect_uri, code_challenge=None):
        raise NotImplementedError

    @abstractmethod
    def exchange_code(self, code, redirect_uri, code_verifier=None):
        raise NotImplementedError

    @abstractmethod
    def refresh_token(self, refresh_token):
        raise NotImplementedError

    @abstractmethod
    def get_accounts(self, access_token):
        raise NotImplementedError

    @abstractmethod
    def sync_profile(self, access_token, account):
        raise NotImplementedError

    @abstractmethod
    def sync_posts(self, access_token, account, limite=25):
        raise NotImplementedError

    @abstractmethod
    def revoke(self, access_token, refresh_token=None):
        raise NotImplementedError

    @abstractmethod
    def check_connection(self, access_token):
        raise NotImplementedError
