# -*- coding: utf-8 -*-
"""
putkiya.py - Rishu Bind API Client
Cleaned library version for zevric_email_tool repo
Original: putkiya_2.py (Rishu Bind Manager)
Base URL: https://rishu-official-bind.vercel.app/api
"""

import requests

_BASE_URL = "https://rishu-official-bind.vercel.app/api"
_EXTRACT_URL = "https://rishu-jwt-gen.vercel.app/rishu"
_APP_ID = "100067"

def _api_request(endpoint, params):
    url = f"{_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=20)
        try:
            return resp.json()
        except:
            return {"success": False, "message": f"Invalid response {resp.status_code}", "raw": resp.text[:500]}
    except Exception as e:
        return {"success": False, "message": f"Network error: {e}"}

def send_otp(token, email):
    return _api_request("send-otp", {"access_token": token, "email": email, "app_id": _APP_ID})

def bind_email(token, email, otp, sec_code):
    return _api_request("bind", {"access_token": token, "email": email, "otp": otp, "secondary_password": sec_code, "app_id": _APP_ID})

def cancel_request(token):
    return _api_request("cancel", {"access_token": token, "app_id": _APP_ID})

def unbind_with_sec(token, sec_code):
    return _api_request("unbind-with-sec", {"access_token": token, "secondary_password": sec_code, "app_id": _APP_ID})

def unbind_with_otp(token, email, otp):
    return _api_request("unbind-with-otp", {"access_token": token, "email": email, "otp": otp, "app_id": _APP_ID})

def change_email_sec(token, old_email, new_email, sec_code, new_otp):
    return _api_request("change-email-sec", {"access_token": token, "old_email": old_email, "new_email": new_email, "secondary_password": sec_code, "new_otp": new_otp, "app_id": _APP_ID})

def change_email_otp(token, old_email, new_email, old_otp, new_otp):
    return _api_request("change-email-otp", {"access_token": token, "old_email": old_email, "new_email": new_email, "old_otp": old_otp, "new_otp": new_otp, "app_id": _APP_ID})

def get_bind_info(token):
    return _api_request("get-bind-info", {"access_token": token, "app_id": _APP_ID})

def get_platforms(token):
    return _api_request("get-platform", {"access_token": token})

def revoke_token_api(token):
    return _api_request("revoke-access", {"access_token": token, "app_id": _APP_ID})

def eat_to_access(eat_token_or_url):
    """Convert EAT URL/token to access token via Garena callback"""
    import urllib.parse
    eat = eat_token_or_url
    if "eat=" in eat_token_or_url:
        try:
            parsed = urllib.parse.urlparse(eat_token_or_url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'eat' in qs:
                eat = qs['eat'][0]
            else:
                eat = eat_token_or_url.split('eat=')[1].split('&')[0]
        except:
            pass
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={eat}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
        final_url = r.url
        parsed_final = urllib.parse.urlparse(final_url)
        final_qs = urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' in final_qs:
            return {"success": True, "access_token": final_qs['access_token'][0], "account_id": final_qs.get('account_id',[None])[0], "nickname": final_qs.get('nickname',[None])[0], "region": final_qs.get('region',[None])[0]}
        return {"success": False, "message": "EAT expired"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def extract_jwt_info(jwt_token):
    try:
        resp = requests.get(_EXTRACT_URL, params={"access_token": jwt_token}, timeout=15)
        return (resp.json(), None) if resp.status_code==200 else (None, f"HTTP {resp.status_code}")
    except Exception as e:
        return None, str(e)
