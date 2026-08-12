"""Test script for the installed smailpro-api package."""

from smailpro_api import SmailProAPI, Provider

def test_google():
    print("Testing Google provider...")
    api = SmailProAPI(
        provider=Provider.GOOGLE,
        solver_url="http://127.0.0.1:9000"
    )
    email_info = api.create_email()
    print(f"Created: {email_info['address']}")
    
    import time
    time.sleep(5)
    
    inbox = api.fetch_inbox(email_info)
    print(f"Inbox messages: {len(inbox.get('messages', []))}")
    return True

if __name__ == "__main__":
    try:
        test_google()
        print("Test PASSED!")
    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()
