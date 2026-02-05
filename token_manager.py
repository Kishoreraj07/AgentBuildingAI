# token_manager.py
import requests
import logging
from config import MAIN_URL

class TokenManager:
    def __init__(self, refresh_token, access_token, on_token_refreshed=None, on_invalid_token=None):
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.on_token_refreshed = on_token_refreshed
        self.on_invalid_token = on_invalid_token
        self.session = requests.Session()
        self._setup_refresh_interceptor()

    def _setup_refresh_interceptor(self):
        def response_hook(response, *args, **kwargs):
            if response.status_code == 401 and "Authorization" in response.request.headers:
                logging.info("Access token expired (401). Attempting refresh...")
                if self._refresh_access_token():
                    # Update header and retry
                    response.request.headers["Authorization"] = f"Bearer {self.access_token}"
                    new_response = self.session.send(response.request)
                    new_response.history.append(response)  # preserve history
                    return new_response
                else:
                    logging.error("Failed to refresh token. Logging out.")
                    if self.on_invalid_token:
                        self.on_invalid_token()
            return response

        self.session.hooks["response"].append(response_hook)

    def _refresh_access_token(self):
        try:
            url = f"{MAIN_URL}/app/account/token/refresh/"
            payload = {"refresh": self.refresh_token}
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access")
                new_refresh = data.get("refresh")
                if new_refresh:
                    self.refresh_token = new_refresh
                if self.on_token_refreshed:
                    self.on_token_refreshed(self.access_token, self.refresh_token)
                return True
            else:
                logging.warning(f"Refresh failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logging.error(f"Exception during token refresh: {e}")
        return False

    # Use these methods everywhere in your app instead of requests.get/post
    def get(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        return self.session.get(url, headers=headers, **kwargs)

    def post(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        return self.session.post(url, headers=headers, **kwargs)

    def put(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        return self.session.put(url, headers=headers, **kwargs)

    def delete(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        return self.session.delete(url, headers=headers, **kwargs)