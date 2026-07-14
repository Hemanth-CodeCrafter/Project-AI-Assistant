import requests

def is_connected():
    try:
        requests.get(
            "https://www.google.com",
            timeout=3
        )
        return True
    except:
        return False