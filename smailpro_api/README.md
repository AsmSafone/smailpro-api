# SmailPro API

A Python wrapper for the [SmailPro](https://smailpro.com) temporary email service, supporting multiple email providers and automated CAPTCHA bypassing via an external solver service.

## Features

- **Multi-Provider Support**: Create temporary emails from Google (Gmail), Microsoft (Outlook/Hotmail), and other providers.
- **Inbox & Message Fetching**: Easily fetch and read emails from created temporary addresses.
- **Configurable CAPTCHA Solver**: Integrates with any Boterdrop-Solver-compatible service. Server URL is fully configurable.
- **Type Hints**: Full type annotations for better IDE support.

## Installation

```bash
pip install smailpro-api
```

## Prerequisites

This library requires a running CAPTCHA solver service to handle Cloudflare Turnstile challenges. The [Boterdrop-Solver](https://github.com/najibyahya/Boterdrop-Solver) is recommended. It can be run via Docker using the `Dockerfile` and `docker-compose.yml` provided in the solver setup.

## Usage

```python
from smailpro_api import SmailProAPI, Provider

# Initialize the API
api = SmailProAPI(
    provider=Provider.GOOGLE,
    solver_url="http://localhost:9000"  # Your solver service URL
)

# Create a new temporary email
email_info = api.create_email()
print(f"Created email: {email_info['address']}")

# Wait for emails to arrive
import time
time.sleep(5)

# Fetch the inbox
inbox = api.fetch_inbox(email_info)
print(f"Found {len(inbox.get('messages', []))} messages.")

# Read a specific message
if inbox.get('messages'):
    first_msg_id = inbox['messages'][0]['mid']
    message_content = api.fetch_message(email_info, first_msg_id)
    print(f"Message body: {message_content.get('body')}")
```

## Supported Providers

| Provider | Default Domain | Available Domains |
| :--- | :--- | :--- |
| `google` | gmail.com | gmail.com, googlemail.com |
| `microsoft` | outlook.com | outlook.com, hotmail.com, outlook.kr, outlook.fr, outlook.com.vn, outlook.co.id, outlook.co.th, outlook.com.ar, outlook.co.il |
| `other` | melbourne.edu.pl | melbourne.edu.pl, sydney.edu.pl, tokyo.edu.pl, storegmail.net |

## Configuration Options

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `provider` | `Provider` | `Provider.GOOGLE` | Email provider to use |
| `solver_url` | `str` | `"http://127.0.0.1:9000"` | URL of the CAPTCHA solver service |
| `session_token` | `Optional[str]` | `None` | Optional session token to bypass CAPTCHA |
| `user_agent` | `str` | Chrome 120 UA | User agent string for requests |
| `captcha_retry_max` | `int` | `2` | Maximum retries for CAPTCHA solving |
| `captcha_poll_interval` | `float` | `2.0` | Interval between CAPTCHA poll requests (seconds) |
| `captcha_poll_timeout` | `int` | `60` | Maximum time to wait for CAPTCHA solving (seconds) |

## Troubleshooting

- **403 Forbidden**: Ensure the solver service is running and accessible. Check that the `solver_url` is correct.
- **CAPTCHA Timeout**: If solving takes too long, increase `captcha_poll_timeout`.
- **Memory Issues (Solver)**: If using Docker for the solver, ensure the container has enough memory allocated.

## License

MIT License
