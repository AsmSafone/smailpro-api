"""
SmailPro API Client - Handles communication with the SmailPro API
and CAPTCHA solver integration.
"""

import requests
import json
import time
from typing import Optional, Dict, List, Any
from enum import Enum


class Provider(str, Enum):
    """Supported email providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OTHER = "other"


PROVIDER_CONFIG = {
    Provider.GOOGLE: {
        'api_path': 'temp_gmail',
        'default_domain': 'gmail.com',
        'domains': ['gmail.com', 'googlemail.com']
    },
    Provider.MICROSOFT: {
        'api_path': 'temp_outlook',
        'default_domain': 'outlook.com',
        'domains': [
            "outlook.com", "hotmail.com", "outlook.kr", "outlook.fr",
            "outlook.com.vn", "outlook.co.id", "outlook.co.th",
            "outlook.com.ar", "outlook.co.il"
        ]
    },
    Provider.OTHER: {
        'api_path': 'temp_email',
        'default_domain': 'melbourne.edu.pl',
        'domains': ["melbourne.edu.pl", "sydney.edu.pl", "tokyo.edu.pl", "storegmail.net"]
    }
}

# Cloudflare Turnstile Sitekey for SmailPro
TURNSTILE_SITEKEY = "0x4AAAAAAABIS_gEec2IwOhI"

# Default solver URL
DEFAULT_SOLVER_URL = "http://127.0.0.1:9000"


class SmailProAPI:
    """
    Client for interacting with the SmailPro temporary email API.
    
    Features:
    - Multi-provider support (Gmail, Outlook, etc.)
    - Automated CAPTCHA bypassing via external solver service
    - Email creation and inbox/message fetching
    
    Example usage:
        api = SmailProAPI(
            provider=Provider.GOOGLE,
            solver_url="http://localhost:9000"
        )
        email = api.create_email()
        inbox = api.fetch_inbox(email)
    """
    
    def __init__(
        self,
        provider: Provider = Provider.GOOGLE,
        solver_url: str = DEFAULT_SOLVER_URL,
        session_token: Optional[str] = None,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        captcha_retry_max: int = 2,
        captcha_poll_interval: float = 2.0,
        captcha_poll_timeout: int = 60
    ):
        """
        Initialize the SmailPro API client.
        
        Args:
            provider: Email provider to use (default: GOOGLE)
            solver_url: URL of the CAPTCHA solver service (default: http://127.0.0.1:9000)
            session_token: Optional session token to bypass CAPTCHA
            user_agent: User agent string for requests
            captcha_retry_max: Maximum retries for CAPTCHA solving
            captcha_poll_interval: Interval between CAPTCHA poll requests (seconds)
            captcha_poll_timeout: Maximum time to wait for CAPTCHA solving (seconds)
        """
        self.base_app_url = "https://smailpro.com/app"
        self.base_api_url = "https://api.sonjj.com/v1"
        self.session = requests.Session()
        self.provider = provider
        self.solver_url = solver_url.rstrip('/')
        self.session_token = session_token
        self.captcha_retry_max = captcha_retry_max
        self.captcha_poll_interval = captcha_poll_interval
        self.captcha_poll_timeout = captcha_poll_timeout
        
        self.user_agent = user_agent
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://smailpro.com",
            "Referer": "https://smailpro.com/temporary-email"
        })

        if self.session_token:
            self._update_session_headers()
            
        self._provider_config = PROVIDER_CONFIG[self.provider]

    def _update_session_headers(self):
        """Update headers with session token."""
        self.session.headers.update({
            "X-Session-Token": self.session_token,
            "X-Token-Type": "fingerprint"
        })

    def set_provider(self, provider: Provider):
        """Change the email provider."""
        if provider in PROVIDER_CONFIG:
            self.provider = provider
            self._provider_config = PROVIDER_CONFIG[self.provider]
        else:
            raise ValueError(f"Invalid provider. Choose from: {list(PROVIDER_CONFIG.keys())}")

    def solve_captcha(self, page_url: str, sitekey: str) -> str:
        """
        Solves Turnstile CAPTCHA using the external solver service.
        
        Args:
            page_url: The URL of the page containing the CAPTCHA
            sitekey: The Turnstile sitekey
            
        Returns:
            The solved CAPTCHA token
            
        Raises:
            Exception: If CAPTCHA solving fails or times out
        """
        # Step 1: Create task
        try:
            submit_resp = requests.get(
                f"{self.solver_url}/turnstile",
                params={"url": page_url, "sitekey": sitekey},
                timeout=10
            )
            submit_resp.raise_for_status()
            submit = submit_resp.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to submit CAPTCHA task to solver: {e}")
        
        task_id = submit.get("task_id")
        if not task_id:
            raise Exception("Failed to submit CAPTCHA task.")
            
        # Step 2: Poll for result
        start_time = time.time()
        while time.time() - start_time < self.captcha_poll_timeout:
            time.sleep(self.captcha_poll_interval)
            try:
                result_resp = requests.get(
                    f"{self.solver_url}/result",
                    params={"id": task_id},
                    timeout=10
                )
                result_resp.raise_for_status()
                result = result_resp.json()
            except requests.RequestException:
                continue
                
            status = result.get("status")
            if status == "success":
                return result.get("value")
            elif status == "error":
                raise Exception(f"CAPTCHA solving failed: {result.get('message')}")
                
        raise Exception("CAPTCHA solving timed out.")

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        require_captcha: bool = True
    ) -> requests.Response:
        """
        Make an HTTP request with automatic CAPTCHA retry.
        
        Args:
            method: HTTP method (GET or POST)
            url: Request URL
            params: URL parameters
            json_data: JSON body for POST requests
            headers: Additional headers
            require_captcha: Whether to attempt CAPTCHA solving on 403
            
        Returns:
            Response object
        """
        _headers = dict(headers) if headers else {}
        
        for attempt in range(self.captcha_retry_max + 1):
            try:
                if method == "GET":
                    response = self.session.get(url, params=params, headers=_headers)
                elif method == "POST":
                    response = self.session.post(url, json=json_data, headers=_headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                if response.status_code == 403:
                    if not require_captcha:
                        response.raise_for_status()
                    raise requests.RequestException("403 Forbidden - CAPTCHA required")
                    
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                if "403" in str(e) and attempt < self.captcha_retry_max:
                    print(f"[{attempt + 1}/{self.captcha_retry_max + 1}] CAPTCHA detected, solving...")
                    
                    # Determine action based on URL
                    action = "smailpro"
                    purpose = "smailpro"
                    if "/app/create" in url:
                        action = "smailpro_create"
                        purpose = "smailpro_create"
                    elif "/app/message" in url:
                        action = "smailpro_message"
                        purpose = "smailpro_message"
                    
                    token = self.solve_captcha("https://smailpro.com/temporary-email", TURNSTILE_SITEKEY)
                    
                    _headers["x-captcha"] = token
                    _headers["x-purpose"] = purpose
                    
                    # Retry the request with captcha token
                    if method == "GET":
                        response = self.session.get(url, params=params, headers=_headers)
                    elif method == "POST":
                        response = self.session.post(url, json=json_data, headers=_headers)
                    
                    if response.status_code == 403:
                        raise requests.RequestException("403 Forbidden - CAPTCHA invalid")
                    response.raise_for_status()
                    return response
                raise

    def create_email(
        self,
        username: str = "random",
        domain: Optional[str] = None,
        server: str = "1",
        email_type: str = "alias"
    ) -> Dict[str, Any]:
        """
        Create a new temporary email address.
        
        Args:
            username: Desired username (use "random" for auto-generated)
            domain: Specific domain (defaults to provider's default)
            server: Server ID
            email_type: Type of email ("alias" or other supported types)
            
        Returns:
            Dictionary with email info including 'address', 'timestamp', and 'key'
        """
        params = {
            "username": username,
            "type": email_type,
            "domain": domain or self._provider_config['default_domain'],
            "server": server
        }
        url = f"{self.base_app_url}/create"
        response = self._make_request("GET", url, params=params)
        return response.json()

    def fetch_inbox(self, email_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch the inbox for a given email address.
        
        Args:
            email_info: Email info dictionary from create_email()
            
        Returns:
            Dictionary containing messages list
        """
        payload_data = [{
            "address": email_info['address'],
            "timestamp": email_info['timestamp'],
            "key": email_info.get('key', '')
        }]
        
        # Get payload from app
        payload_url = f"{self.base_app_url}/inbox"
        payload_resp = self._make_request("POST", payload_url, json_data=payload_data)
        payload = payload_resp.json()[0]['payload']
        
        # Fetch inbox from API
        api_path = self._provider_config['api_path']
        api_url = f"{self.base_api_url}/{api_path}/inbox"
        response = self._make_request("GET", api_url, params={"payload": payload})
        return response.json()

    def fetch_message(self, email_info: Dict[str, Any], message_id: str) -> Dict[str, Any]:
        """
        Fetch the full content of a specific message.
        
        Args:
            email_info: Email info dictionary from create_email()
            message_id: The message ID
            
        Returns:
            Dictionary containing the full message content
        """
        # Get payload from app
        payload_url = f"{self.base_app_url}/message"
        params = {"email": email_info['address'], "mid": message_id}
        payload_resp = self._make_request("GET", payload_url, params=params)
        payload = payload_resp.json().get('payload')
        
        # Fetch message from API
        api_path = self._provider_config['api_path']
        api_url = f"{self.base_api_url}/{api_path}/message"
        response = self._make_request("GET", api_url, params={"payload": payload})
        return response.json()
