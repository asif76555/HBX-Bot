#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
⚡ HBX COOKIE CONVERTER & PUSH BOT ⚡
Version: 4.2 (CF Bypass/Termux Ready)
Created: For Termux Mobile Usage
Run: python bot.py
========================================
"""

import asyncio
import logging
import random
import os
import csv
import json
import time
import pyotp
import instaloader
import requests
import io
import aiohttp
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler
)

# =============================================================
# ⚙️ সেটিংস
# =============================================================
TARGET_URL = "http://skysysx.net/e/thanatos"
INFO_URL = "http://skysysx.net/api/info"
STATUS_URL = "http://skysysx.net/api/status"
ADMIN_LOG_CHAT_ID = "-1003894606555"
DEVELOPER = "ASIF"
ADMIN_IDS = [8700692998]
MAX_ACCOUNTS = 100
SPAM_WINDOW = 60
SPAM_MAX = 10
MAX_LOGIN_WORKERS = 20
SIGNAL_CHECK_INTERVAL = 15
DEV_TAG = "▰▰▰▰▰ 𝙳𝙴𝚅 𝙱𝚈 𝙰𝚂𝙸𝙵 ▰▰▰▰▰"
TOKEN_FILE = "bot_token.txt"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================================
# 🎭 কথোপকথনের ধাপ
# =============================================================
(
    MENU,
    CP_USERNAMES,
    CP_PASS_TYPE,
    CP_SAME_PASS,
    CP_DIFF_PASS,
    CP_2FA,
    OP_DATA,
) = range(7)

# =============================================================
# 💾 ডাটাবেজ
# =============================================================
user_db = {}
spam_tracker = {}
banned_users = set()
registered_users = set()
daily_stats = {
    'date': datetime.now().strftime("%Y-%m-%d"),
    'total_push': 0, 'total_success': 0,
    'total_failed': 0, 'active_users': set(),
}
api_status_cache = {
    'online': False, 'push_locked': False,
    'last_notified_state': None, 'http_code': 0,
    'last_check': None, 'uptime_start': None,
}

# =============================================================
# 🎨 ফানি মেসেজ
# =============================================================
BARS = [
    "▱▱▱▱▱▱▱▱▱▱", "▰▱▱▱▱▱▱▱▱▱",
    "▰▰▱▱▱▱▱▱▱▱", "▰▰▰▱▱▱▱▱▱▱",
    "▰▰▰▰▱▱▱▱▱▱", "▰▰▰▰▰▱▱▱▱▱",
    "▰▰▰▰▰▰▱▱▱▱", "▰▰▰▰▰▰▰▱▱▱",
    "▰▰▰▰▰▰▰▰▱▱", "▰▰▰▰▰▰▰▰▰▱",
    "▰▰▰▰▰▰▰▰▰▰",
]
SPINNERS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

FUNNY_LIMIT = [
    "😂 ভাই ১০০টার বেশি দিলে আমি পাগল হয়ে যাবো! প্রথম ১০০টা নিচ্ছি 😅",
    "🤣 সুপারম্যান ভাবো নাকি নিজেকে? ১০০টাই দাও বস!",
    "💀 এত একাউন্ট?! প্রসেসর পুড়ে যাবে! ১০০টা রাখলাম!",
    "😤 লোভ কইরো না! একবারে ১০০টা, বেশি না!",
    "🫠 মরে যাবো নাকি?! ১০০টার বেশি দিও না প্লিজ!",
]

FUNNY_COOKIE_WAIT = [
    "🔥 ইনস্টাগ্রামের সাথে মারামারি চলছে...",
    "💎 কুকি চুরির অপারেশন চলমান...",
    "⚡ সুপার স্পিডে কাজ হচ্ছে! চা খাও!",
    "🚀 রকেট স্পিডে লগইন হচ্ছে...",
    "👑 রাজার মতো কুকি বের হচ্ছে...",
    "🌟 ইঞ্জিন জ্বলছে... অপেক্ষা করো!",
    "💪 একাউন্টগুলো পালাতে চাচ্ছে কিন্তু ধরে ফেলছি!",
    "🍳 কুকি ভাজা হচ্ছে... গরম গরম আসবে!",
    "🎣 মাছ ধরার মতো কুকি ধরছি...",
    "🧙 জাদু করে কুকি বের করছি... আবরা কাদাবরা!",
]

FUNNY_API_DEAD = [
    "😂 চায়না মামা ঘুমাইতেছে! 😴💤",
    "🤣 API বাবাজি নাক ডাকাচ্ছে! পরে আসো! 😴",
    "💀 সার্ভার ঘুমের দেশে! কুকি রাখো পরে পুশ দিও! 😂",
    "😤 API ভাই বলছে 'ডিস্টার্ব করো না!' কুকি নামাও! 🛌",
    "🦥 API আলসেমি করতেছে! কুকি নিয়ে পরে আসো!",
]

FUNNY_CANCEL = [
    "😂 আরে মামা! পালাচ্ছো কেন?! পরে আসিও! 🏃💨",
    "🤣 ভয় পাইসো নাকি?! কোনো সমস্যা নাই! 😎",
    "😭 চলে যাচ্ছে?! আমি কান্না করবো! পরে আসিও!",
    "🤗 ঠিক আছে মামা! পরে আসলে আবার হেল্প করবো!",
    "👋 বিদায়! আবার আসবে জানি! আমি অপেক্ষায় থাকবো!",
    "😤 রাগ করসো নাকি? কাজ করতে চাও না? ঠিক আছে!",
    "🎭 নাটক করতেছো? ক্যান্সেল করলা কেন মামা?!",
]

FUNNY_CP_ASK = [
    "👑 কুকি চোরের রাজা আইসা গেছে!\nইউজারনেম দাও মামা! 🔥",
    "🔥 কুকি মাফিয়া আইসা গেছে!\nডন বলো কার ইউজারনেম লাগবে! 😎",
    "💎 বস আইসা গেছে!\nইউজারনেম দাও, কুকি বের করি! 🍪",
    "🍪 কুকি মনস্টার আইসা গেছে!\nইউজারনেম দাও নম নম নম! 😋",
    "🥷 নিনজা মোড অন!\nইউজারনেম দাও, কুকি চুরি শুরু হবে! 🔓",
]

FUNNY_OP_ASK = [
    "⚡ পুশ মাস্টার আইসা গেছে!\nডাটা দাও, ফুল ভলিউমে পুশ দিবো! 🚀",
    "🚀 রকেট রেডি!\nডাটা দাও মামা, পুশ দিয়ে দিচ্ছি! 💪",
    "💪 পুশ করবো?\nবলো কত জোরে! ডাটা দাও! 🏋️",
    "🎯 টার্গেট রেডি!\nডাটা দাও, একদম বুলেট স্পিডে পুশ! ⚡",
]

FUNNY_PASS_ASK = [
    "🔑 পাসওয়ার্ড দাও মামা!\nলক খুলতে হবে! 🔓",
    "🗝️ চাবি দাও বস!\nতালা ভাঙতে হবে! 💪",
    "🔐 সিক্রেট কোড দাও!\nসব তালা খুলে ফেলবো! 😎",
]

FUNNY_2FA_ASK = [
    "🔐 2FA কোড দাও মামা!\nএই ডবল তালা খুলতে হবে! 🗝️",
    "🛡️ 2FA কী দাও!\nএই দেয়াল ভাঙতে হবে! 💪",
    "🔑 2FA সিক্রেট দাও!\nনেই? তাহলে NO লেখো! 😅",
]

FUNNY_COMPLETE = [
    "🎊 মিশন সাকসেসফুল মামা!",
    "🏆 চ্যাম্পিয়ন! কাজ শেষ!",
    "🎯 টার্গেট হিট! সব শেষ!",
    "🥇 গোল্ড মেডেল! কাজ হয়ে গেছে!",
]

FUNNY_PUSH_WAIT = [
    "🚀 সার্ভারে রকেট পাঠাচ্ছি...",
    "📡 স্যাটেলাইট দিয়ে পুশ হচ্ছে...",
    "⚡ বিদ্যুৎ গতিতে পুশ চলছে...",
    "🌊 পুশের ঢেউ চলছে সার্ভারে...",
]


def get_bar(done, total):
    if total == 0:
        return BARS[0]
    return BARS[min(int((done / total) * 10), 10)]


def now_time():
    return datetime.now().strftime("%I:%M %p")


def register_user(user):
    uid = user.id
    if uid not in user_db:
        user_db[uid] = {
            'username': user.username or f"ID_{uid}",
            'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'joined': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'total_push': 0, 'total_success': 0,
            'total_failed': 0, 'banned': False,
        }
    else:
        user_db[uid]['username'] = user.username or f"ID_{uid}"
        user_db[uid]['full_name'] = f"{user.first_name or ''} {user.last_name or ''}".strip()
    registered_users.add(uid)
    return user_db[uid]


def check_spam(uid):
    now = time.time()
    if uid not in spam_tracker:
        spam_tracker[uid] = []
    spam_tracker[uid] = [t for t in spam_tracker[uid] if now - t < SPAM_WINDOW]
    if len(spam_tracker[uid]) >= SPAM_MAX:
        w = int(SPAM_WINDOW - (now - spam_tracker[uid][0])) + 1
        return True, max(w, 1)
    spam_tracker[uid].append(now)
    return False, 0


def update_stats(uid, push, success, failed):
    today = datetime.now().strftime("%Y-%m-%d")
    if daily_stats['date'] != today:
        daily_stats.update({
            'date': today, 'total_push': 0,
            'total_success': 0, 'total_failed': 0,
            'active_users': set(),
        })
    daily_stats['total_push'] += push
    daily_stats['total_success'] += success
    daily_stats['total_failed'] += failed
    daily_stats['active_users'].add(uid)


def cancel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ বাতিল করো", callback_data="cancel_op")]
    ])


# =============================================================
# 🔥 CLOUDFLARE BYPASS PUSH ENGINE (curl_cffi - Termux Ready)
# =============================================================

try:
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except Exception as e:
    CURL_CFFI_AVAILABLE = False
    logger.warning(f"⚠️ curl_cffi import failed! Error: {e}. Run: pkg install libcurl")


class HttpPushEngine:
    """
    Cloudflare Bypass Push Engine using curl_cffi!
    Impersonates Chrome TLS fingerprint to bypass CF 403/503.
    """
    
    # 🔒 STRICT ENDPOINT LOCK
    STRICT_PUSH_URL = "http://skysysx.net/e/thanatos"
    
    def __init__(self):
        self._session = None
        
    async def _get_session(self):
        """Get or create curl_cffi async session"""
        if self._session is None:
            if CURL_CFFI_AVAILABLE:
                self._session = AsyncSession(impersonate="chrome120")
            else:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=45)
                )
        return self._session
        
    async def close(self):
        """Cleanup"""
        if self._session:
            await self._session.close()
            self._session = None
            
    async def health_check(self) -> dict:
        """Check if push server is online"""
        result = {
            'online': False,
            'push_locked': False,
            'api_offline': True,
            'http_code': 0,
            'latency_ms': 0
        }
        
        start_time = time.time()
        try:
            session = await self._get_session()
            
            if CURL_CFFI_AVAILABLE and isinstance(session, AsyncSession):
                resp = await session.get(INFO_URL, timeout=45)
                latency = int((time.time() - start_time) * 1000)
                result['latency_ms'] = latency
                result['http_code'] = resp.status_code
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if data.get('push_locked'):
                            result['push_locked'] = True
                            return result
                        if data.get('api_offline_locked') or data.get('webhook_status') == 'fail':
                            result['api_offline'] = True
                            return result
                        result['online'] = True
                        result['api_offline'] = False
                    except json.JSONDecodeError:
                        result['online'] = True
                        result['api_offline'] = False
            else:
                async with session.get(INFO_URL) as resp:
                    latency = int((time.time() - start_time) * 1000)
                    result['latency_ms'] = latency
                    result['http_code'] = resp.status
                    if resp.status == 200:
                        try:
                            data = await resp.json(content_type=None)
                            if data.get('push_locked'):
                                result['push_locked'] = True
                                return result
                            if data.get('api_offline_locked') or data.get('webhook_status') == 'fail':
                                result['api_offline'] = True
                                return result
                            result['online'] = True
                            result['api_offline'] = False
                        except json.JSONDecodeError:
                            result['online'] = True
                            result['api_offline'] = False
                            
        except Exception as e:
            logger.debug(f"Health check error: {e}")
            
        return result
        
    async def execute_push(self, converted_list):
        result = {
            'success': False, 'job_id': None, 'server_success': 0,
            'server_failed': 0, 'already_submitted': 0, 'error': None,
            'api_offline': False, 'push_locked': False,
        }
        session = await self._get_session()
        if not converted_list:
            result['error'] = "No data to push!"
            return result
        health = await self.health_check()
        if not health['online']:
            result['api_offline'] = True
            result['error'] = "সার্ভারে কানেক্ট হচ্ছে না!"
            return result
        if health['push_locked']:
            result['push_locked'] = True
            result['error'] = "অর্ডার বন্ধ!"
            return result
            
        payload_lines = [item.get('converted', '').strip() for item in converted_list if item.get('converted', '').strip()]
        if not payload_lines:
            result['error'] = "Empty payload after cleaning"
            return result
        payload_text = '\n'.join(payload_lines)
        logger.info(f"[CF_PUSH] Sending {len(payload_lines)} items to: {self.STRICT_PUSH_URL}")
        
        try:
            if CURL_CFFI_AVAILABLE and isinstance(session, AsyncSession):
                resp = await session.post(url=self.STRICT_PUSH_URL, data={'target': payload_text}, timeout=45, allow_redirects=True, verify=False)
                body = resp.text
                status_code = resp.status_code
            else:
                form_data = aiohttp.FormData()
                form_data.add_field('target', payload_text)
                async with session.post(url=self.STRICT_PUSH_URL, data=form_data, allow_redirects=True, ssl=False) as resp:
                    body = await resp.text()
                    status_code = resp.status
                    
            if status_code in [200, 201, 202]:
                try:
                    data = json.loads(body)
                    result['success'] = True
                    result['job_id'] = data.get('job_id')
                    result['already_submitted'] = data.get('duplicates', 0)
                    if result['job_id']:
                        poll_result = await self._poll_job(result['job_id'])
                        result['server_success'] = poll_result.get('success_count', 0)
                        result['server_failed'] = poll_result.get('failed_count', 0)
                        result['already_submitted'] = poll_result.get('already_submitted', result['already_submitted'])
                    else:
                        result['server_success'] = data.get('success', len(converted_list))
                except json.JSONDecodeError:
                    result['success'] = True
                    result['server_success'] = len(converted_list)
            elif status_code == 409:
                result['error'] = "ALREADY_SUBMITTED"
                result['already_submitted'] = len(converted_list)
            elif status_code == 400:
                try:
                    err = json.loads(body)
                    result['error'] = err.get('error', f"Bad request ({status_code})")
                except:
                    result['error'] = f"HTTP {status_code}"
            elif status_code == 429:
                result['error'] = "Rate limited! Wait 30 seconds."
            elif status_code == 403:
                result['error'] = f"Cloudflare Block (403)! Check bypass."
            elif status_code in [502, 503]:
                result['error'] = f"Server busy/Down ({status_code})"
            else:
                result['error'] = f"HTTP {status_code}: {body[:80]}"
        except asyncio.TimeoutError:
            result['error'] = "Server timeout!"
        except Exception as e:
            logger.error(f"[PUSH] Endpoint failed: {str(e)}")
            result['error'] = f"Connection Error: {str(e)[:50]}"
        return result
        
    async def _poll_job(self, job_id, max_wait=180):
        url = f"{STATUS_URL}/{job_id}"
        start_time = time.time()
        session = await self._get_session()
        default_return = {'success_count': 0, 'failed_count': 0, 'already_submitted': 0}
        try:
            while True:
                elapsed = time.time() - start_time
                if elapsed > max_wait: return default_return
                try:
                    if CURL_CFFI_AVAILABLE and isinstance(session, AsyncSession):
                        resp = await session.get(url, timeout=15)
                        if resp.status_code != 200:
                            await asyncio.sleep(3); continue
                        data = resp.json()
                    else:
                        async with session.get(url, timeout=15) as resp:
                            if resp.status != 200:
                                await asyncio.sleep(3); continue
                            data = await resp.json(content_type=None)
                    status_val = data.get('status')
                    if status_val == 'done':
                        d = data.get('data', {})
                        return {'success_count': d.get('success_count', 0), 'failed_count': d.get('failed_count', 0), 'already_submitted': d.get('already_submitted', 0)}
                    elif status_val == 'staging': await asyncio.sleep(8)
                    elif status_val == 'processing': await asyncio.sleep(2)
                    elif status_val == 'failed':
                        d = data.get('data', {})
                        return {'success_count': d.get('success_count', 0), 'failed_count': d.get('failed_count', 1), 'already_submitted': 0}
                    else: await asyncio.sleep(3)
                except asyncio.TimeoutError: await asyncio.sleep(5)
                except Exception: await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            return default_return

push_engine = HttpPushEngine()

async def browser_push(converted_list):
    return await push_engine.execute_push(converted_list)


# =============================================================
# 🍪 ইনস্টাগ্রাম লগইন 
# =============================================================
def _do_ig_login(username, password, two_fa_key):
    result = {
        'success': False, 'cookie_string': None,
        'cookie_dict': None, 'error': None,
        'username': username, 'password': password,
    }
    try:
        L = instaloader.Instaloader(quiet=True, download_pictures=False, download_videos=False, download_video_thumbnails=False, download_geotags=False, download_comments=False, save_metadata=False, compress_json=False)
        L.context._session.headers.update({'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1', 'Accept-Language': 'en-US,en;q=0.9'})
        time.sleep(random.uniform(0.3, 0.8))
        try:
            L.login(username, password)
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            if two_fa_key and two_fa_key.upper() not in ('NO', 'NONE', ''):
                try:
                    clean = two_fa_key.replace(" ", "").replace("-", "")
                    otp = pyotp.TOTP(clean).now()
                    L.two_factor_login(otp)
                except Exception as e:
                    result['error'] = f"2FA ভুল: {str(e)[:40]}"; return result
            else:
                result['error'] = "2FA কোড লাগবে মামা!"; return result
        except instaloader.exceptions.BadCredentialsException:
            result['error'] = "পাসওয়ার্ড ভুল দিসো মামা! 🤦"; return result
        except instaloader.exceptions.ConnectionException as e:
            err = str(e).lower()
            if 'checkpoint' in err: result['error'] = "চেকপয়েন্ট! ভেরিফাই লাগবে 📧"
            elif 'rate' in err or 'wait' in err: result['error'] = "ইনস্টাগ্রাম বলছে পরে আসো! 🐢"
            elif 'getaddrinfo' in err or 'connection' in err: result['error'] = "ইন্টারনেট সমস্যা! 🌐"
            else: result['error'] = f"কানেকশন: {str(e)[:35]}"
            return result
        except Exception as e:
            result['error'] = f"লগইন: {str(e)[:35]}"; return result
        if not L.context.is_logged_in:
            result['error'] = "লগইন হয়নি! 🤔"; return result
        cookies = L.context._session.cookies.get_dict()
        if 'sessionid' not in cookies:
            result['error'] = "সেশন পাই নাই! 😤"; return result
        result['success'] = True
        result['cookie_dict'] = cookies
        result['cookie_string'] = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        return result
    except Exception as e:
        result['error'] = f"অপ্রত্যাশিত: {str(e)[:40]}"; return result

async def ig_login_async(username, password, two_fa, loop=None):
    if loop is None: loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, _do_ig_login, username, password, two_fa)


# =============================================================
# 🌐 সিগন্যাল (API Status Check)
# =============================================================
def build_online_msg():
    return "✨✅ ইনস্টাগ্রাম চালু আছে ✅ ✨\n━━━━━━━━━━━━━━━━━━━━━\n\n🔥 অবস্থা: ফুল একটিভ ✅\n📊 HTTP: 200 OK\n⚡ গতি: আলটা হাই 🚀\n\nসবাই ফুল স্পিডে কাজ শুরু করো! ⚡\n━━━━━━━━━━━━━━━━━━━━━\n" + f"🕒 সময়: {now_time()}"

def build_offline_msg(reason="api_offline", code=0):
    if reason == "push_locked":
        return "✨⛔ অর্ডার বন্ধ ⛔ ✨\n━━━━━━━━━━━━━━━━━━━━━\n\n🚫 অবস্থা: অর্ডার শেষ ⛔\n📉 কারণ: আজকের কোটা ফুরাইছে\n\nআগামীকাল আবার আসো মামা 🙏\n━━━━━━━━━━━━━━━━━━━━━\n" + f"🕒 সময়: {now_time()}"
    return "✨❌ ইনস্টাগ্রাম বন্ধ ❌ ✨\n━━━━━━━━━━━━━━━━━━━━━\n\n" + f"🚫 অবস্থা: কাজ বন্ধ ❌\n🚫 HTTP: {code} ⚠️\n📉 কারণ: সার্ভার মামা ঘুমাচ্ছে\n\nসবাই কাজ বন্ধ করো! ❌\n━━━━━━━━━━━━━━━━━━━━━\n" + f"🕒 সময়: {now_time()}"

async def check_api_live(app):
    while True:
        try:
            health = await push_engine.health_check()
            st = "api_offline"
            if health['online']: st = "online"
            elif health['push_locked']: st = "push_locked"
            last = api_status_cache.get('last_notified_state')
            if last is not None and st != last:
                if st == "online": msg = build_online_msg(); api_status_cache['uptime_start'] = datetime.now()
                elif st == "push_locked": msg = build_offline_msg("push_locked", health['http_code'])
                else: msg = build_offline_msg("api_offline", health['http_code'])
                bad = set()
                for cid in registered_users.copy():
                    try: await app.bot.send_message(chat_id=cid, text=msg); await asyncio.sleep(0.05)
                    except Exception: bad.add(cid)
                registered_users -= bad
            if st == "online" and not api_status_cache.get('uptime_start'): api_status_cache['uptime_start'] = datetime.now()
            api_status_cache.update({'last_notified_state': st, 'online': st == "online", 'push_locked': st == "push_locked", 'http_code': health['http_code'], 'last_check': now_time()})
        except Exception as e: logger.error(f"Signal error: {e}")
        await asyncio.sleep(SIGNAL_CHECK_INTERVAL)


# =============================================================
# 🍪 কুকি বের করার ইঞ্জিন
# =============================================================
async def extract_cookies(accounts, status_msg, uid, cancel_flag):
    stats = {'total': len(accounts), 'login_success': 0, 'login_failed': 0, 'cookie_results': [], 'failed_accounts': [], 'retry_accounts': [], 'cancelled': False}
    loop = asyncio.get_running_loop()
    sem = asyncio.Semaphore(MAX_LOGIN_WORKERS)
    done = [0]; lock = asyncio.Lock(); last_edit = [0]

    async def do_one(acc):
        if cancel_flag.get('cancelled'): return
        u, p, tfa = acc['username'], acc['password'], acc.get('two_fa', 'NO')
        async with sem:
            if cancel_flag.get('cancelled'): return
            r = await ig_login_async(u, p, tfa, loop)
            async with lock:
                done[0] += 1; cur = done[0]
                if not r['success']:
                    stats['login_failed'] += 1
                    stats['failed_accounts'].append({'username': u, 'password': p, 'two_fa': tfa, 'reason': r.get('error', '?')})
                    stats['retry_accounts'].append({'username': u, 'password': p, 'two_fa': tfa, 'error': r.get('error', '?')})
                else:
                    stats['login_success'] += 1
                    stats['cookie_results'].append({'username': u, 'password': p, 'cookie_string': r['cookie_string'], 'cookie_dict': r['cookie_dict']})
                now_ts = time.time()
                if now_ts - last_edit[0] > 1.5 or cur <= 3 or cur == stats['total']:
                    last_edit[0] = now_ts; bar = get_bar(cur, stats['total']); pct = int((cur / stats['total']) * 100); sp = SPINNERS[cur % len(SPINNERS)]; fw = random.choice(FUNNY_COOKIE_WAIT)
                    try:
                        await status_msg.edit_text(f"╔══════════════════════════╗\n  🍪✨ কুকি বের হচ্ছে ✨🍪  \n╚══════════════════════════╝\n\n{sp} {fw}\n\n📊 {bar} {pct}%\n\n┌─── 🍪 কুকি রিপোর্ট ─────┐\n│ 📌 মোট     : {stats['total']:>4}          │\n│ ✅ পেয়েছি  : {stats['login_success']:>4}          │\n│ ❌ পাইনি   : {stats['login_failed']:>4}          │\n└──────────────────────────┘\n\n🔐 [{cur}/{stats['total']}] {u[:22]}", reply_markup=cancel_kb())
                    except Exception: pass
    tasks = [do_one(acc) for acc in accounts]
    await asyncio.gather(*tasks, return_exceptions=True)
    if cancel_flag.get('cancelled'): stats['cancelled'] = True
    return stats


# =============================================================
# 📤 ফাইল পাঠানো
# =============================================================
async def send_cookie_file(ctx, uid, stats):
    if not stats['cookie_results']: return
    try:
        lines = [f"{r['username']}|{r['password']}|{r['cookie_string']}" for r in stats['cookie_results']]
        data = "\n".join(lines).encode('utf-8')
        await ctx.bot.send_document(chat_id=uid, document=io.BytesIO(data), filename=f"HBX_cookies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", caption=f"🍪 *কুকি ফাইল*\n━━━━━━━━━━━━━━━\n✅ মোট কুকি: {stats['login_success']}\n📌 ফরম্যাট: `username|password|cookie`\n⚡ সরাসরি ONLY PUSH এ দিতে পারবে!\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n_{DEV_TAG}_", parse_mode='Markdown')
    except Exception as e: logger.error(f"Cookie file error: {e}")

async def send_failed_csv(ctx, uid, stats):
    if not stats['retry_accounts']: return
    try:
        out = io.StringIO(); w = csv.writer(out); w.writerow(['Username', 'Password', '2FA Key', 'Reason'])
        for a in stats['retry_accounts']: w.writerow([a['username'], a['password'], a.get('two_fa', 'NO'), a.get('error', '?')])
        data = out.getvalue().encode('utf-8')
        await ctx.bot.send_document(chat_id=uid, document=io.BytesIO(data), filename=f"HBX_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", caption=f"📋 *Failed Accounts*\n━━━━━━━━━━━━━━━\n❌ Failed: {len(stats['retry_accounts'])}\n\n_{DEV_TAG}_", parse_mode='Markdown')
    except Exception as e: logger.error(f"CSV error: {e}")

async def send_admin_log(ctx, uid, tg_user, full_name, stats, push_r=None):
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); out = io.StringIO(); w = csv.writer(out)
        w.writerow(['Date', 'Time', 'Telegram', 'Name', 'ID', 'Account', 'Status', 'Push'])
        ps = 'Not Done'
        if push_r:
            if push_r.get('success'): ps = 'Pushed'
            elif push_r.get('api_offline'): ps = 'API Down'
        for r in stats.get('cookie_results', []): w.writerow([datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), f"@{tg_user}", full_name, uid, r['username'], 'Success', ps])
        for r in stats.get('retry_accounts', []): w.writerow([datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), f"@{tg_user}", full_name, uid, r['username'], f"Fail:{r.get('error','?')}", ps])
        pi = ""
        if push_r and push_r.get('success'): pi = f"\n✅Push:{push_r.get('server_success',0)} ❌:{push_r.get('server_failed',0)}"
        elif push_r and push_r.get('api_offline'): pi = "\n🔴Push:API Down"
        data = out.getvalue().encode('utf-8')
        await ctx.bot.send_document(chat_id=ADMIN_LOG_CHAT_ID, document=io.BytesIO(data), filename=f"report_{tg_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", caption=f"📊 Report\n📅{now}\n👤@{tg_user}|{full_name}\n🆔{uid}\n✅Cookies:{stats.get('login_success',0)}\n❌Failed:{stats.get('login_failed',0)}{pi}")
    except Exception as e: logger.error(f"Admin log error: {e}")


# =============================================================
# 🎹 কীবোর্ড
# =============================================================
def main_kb():
    return ReplyKeyboardMarkup([[KeyboardButton("🍪 COOKIES + PUSH")], [KeyboardButton("⚡ ONLY PUSH")]], resize_keyboard=True)

def cancel_kb_reply():
    return ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল করো")]], resize_keyboard=True)


# =============================================================
# ❌ বাতিল হ্যান্ডলার
# =============================================================
async def do_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    funny = random.choice(FUNNY_CANCEL)
    cf = context.user_data.get('cancel_flag')
    if cf: cf['cancelled'] = True
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(f"{funny}\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=main_kb())
    elif update.message:
        await update.message.reply_text(f"{funny}\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=main_kb())
    return MENU


# =============================================================
# 🏠 স্টার্ট
# =============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user; register_user(user); context.user_data.clear()
    if user.id in banned_users:
        await update.message.reply_text("⛔ তোমাকে ব্লক করা হয়েছে মামা!"); return ConversationHandler.END
    name = user.first_name or user.username or "বন্ধু"
    welcome = f"⚡ 「 𝙷𝙱𝚇 𝙲𝙾𝙾𝙺𝙸𝙴 𝙲𝙾𝙽𝚅𝙴𝚁𝚃𝙴𝚁 」 ⚡\n━━━━━━━━━━━━━━━━━━━━\n👋 আরে {name} মামা!, আমি জানতাম তুমি আসবে!\nকুকি ফাইল (.txt) দাও, আমি কনভার্ট করে পুশ দিচ্ছি।\n━━━━━━━━━━━━━━━━━━━━\n📢 [💠【 𝙷𝙱𝚇 • 𝙼𝙰𝚁𝙺𝙴𝚃𝙸𝙽𝙶 】💠](https://t.me/hbx_marketiing)\n💬 [💠【 𝙷𝙱𝚇 • 𝙼𝙰𝚁𝙺𝙴𝚃𝙸𝙽𝙶 𝙲𝙷𝙰𝚃 】💠](https://t.me/hbx_marketingChat)\n━━━━━━━━━━━━━━━━━━━━\n_{DEV_TAG}_"
    await update.message.reply_text(welcome, reply_markup=main_kb(), parse_mode='Markdown', disable_web_page_preview=True)
    return MENU

# =============================================================
# 🍪 COOKIES + PUSH Flow
# =============================================================
async def cp_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['mode'] = 'cp'; await update.message.reply_text(f"{random.choice(FUNNY_CP_ASK)}", reply_markup=cancel_kb_reply()); return CP_USERNAMES

async def cp_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.strip() == "❌ বাতিল করো": return await do_cancel(update, context)
    c = ""
    if update.message.document:
        try: f = await update.message.document.get_file(); c = (await f.download_as_bytearray()).decode('utf-8', errors='replace')
        except Exception as e: await update.message.reply_text(f"❌ File error: {e}", reply_markup=cancel_kb_reply()); return CP_USERNAMES
    elif update.message.text: c = update.message.text
    if not c.strip(): await update.message.reply_text("❌ Empty! Give usernames please! 😤", reply_markup=cancel_kb_reply()); return CP_USERNAMES
    users = [u.strip() for u in c.split('\n') if u.strip()]
    if not users: await update.message.reply_text("❌ No usernames found! 🤷", reply_markup=cancel_kb_reply()); return CP_USERNAMES
    if len(users) > MAX_ACCOUNTS: await update.message.reply_text(f"{random.choice(FUNNY_LIMIT)}\n\nYou sent: `{len(users)}`\nTaking first *100* only! 😉", parse_mode='Markdown', reply_markup=cancel_kb_reply()); users = users[:MAX_ACCOUNTS]
    context.user_data['usernames'] = users
    await update.message.reply_text(f"✅ *{len(users)} usernames received!*\n\n🔑 How will you give passwords?", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Same Password", callback_data="pass_same")], [InlineKeyboardButton("🔀 Different Passwords", callback_data="pass_diff")]]))
    return CP_PASS_TYPE

async def cp_pass_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query; await q.answer()
    if q.data == "pass_same": context.user_data['pass_type'] = 'same'; await q.message.reply_text(f"{random.choice(FUNNY_PASS_ASK)}\nOne for all! 😎", reply_markup=cancel_kb_reply()); return CP_SAME_PASS
    context.user_data['pass_type'] = 'diff'; n = len(context.user_data['usernames']); await q.message.reply_text(f"{random.choice(FUNNY_PASS_ASK)}\n*{n}* needed - One per line! 📝", parse_mode='Markdown', reply_markup=cancel_kb_reply()); return CP_DIFF_PASS

async def cp_same(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.strip() == "❌ বাতিল করো": return await do_cancel(update, context)
    pw = (update.message.text or "").strip()
    if not pw: await update.message.reply_text("❌ Empty password?! Give it please! 🤦", reply_markup=cancel_kb_reply()); return CP_SAME_PASS
    context.user_data['passwords'] = [pw] * len(context.user_data['usernames']); await update.message.reply_text(f"✅ Password Set!\n\n{random.choice(FUNNY_2FA_ASK)}", reply_markup=cancel_kb_reply()); return CP_2FA

async def cp_diff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.strip() == "❌ বাতিল করো": return await do_cancel(update, context)
    c = ""
    if update.message.document:
        try: f = await update.message.document.get_file(); c = (await f.download_as_bytearray()).decode('utf-8', errors='replace')
        except Exception: await update.message.reply_text("❌ File error!", reply_markup=cancel_kb_reply()); return CP_DIFF_PASS
    elif update.message.text: c = update.message.text
    pws = [p.strip() for p in c.split('\n') if p.strip()]; users = context.user_data['usernames']
    if len(pws) < len(users): await update.message.reply_text(f"❌ Not enough passwords!\nUsers: `{len(users)}` | Pwds: `{len(pws)}`\nTry again! 😤", parse_mode='Markdown', reply_markup=cancel_kb_reply()); return CP_DIFF_PASS
    context.user_data['passwords'] = pws[:len(users)]; await update.message.reply_text(f"✅ *{len(pws)}* passwords received!\n\n{random.choice(FUNNY_2FA_ASK)}", parse_mode='Markdown', reply_markup=cancel_kb_reply()); return CP_2FA

async def cp_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.strip() == "❌ বাতিল করো": return await do_cancel(update, context)
    uid = update.effective_user.id; tg_user = update.effective_user.username or f"ID_{uid}"; full_name = (f"{update.effective_user.first_name or ''} {update.effective_user.last_name or ''}").strip()
    c = ""
    if update.message.document:
        try: f = await update.message.document.get_file(); c = (await f.download_as_bytearray()).decode('utf-8', errors='replace')
        except Exception: await update.message.reply_text("❌ File error!", reply_markup=cancel_kb_reply()); return CP_2FA
    elif update.message.text: c = update.message.text
    users = context.user_data['usernames']; pws = context.user_data['passwords']; txt = c.strip()
    if txt.upper() in ('NO', 'NONE', ''): tfas = ['NO'] * len(users)
    else: tfas = [k.strip() for k in txt.split('\n') if k.strip()]; 
    while len(tfas) < len(users): tfas.append('NO')
    tfas = tfas[:len(users)]
    accounts = [{'username': u, 'password': pws[i], 'two_fa': tfas[i]} for i, u in enumerate(users)]
    cancel_flag = {'cancelled': False}; context.user_data['cancel_flag'] = cancel_flag
    status = await update.message.reply_text(f"╔══════════════════════════╗\n  🍪✨ Extracting Cookies ✨🍪  \n╚══════════════════════════╝\n\n🚀 Mission started! Total: {len(accounts)} items\n⚡ Running 20 simultaneously!\n\n⏳ Please wait...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_op")]]))
    stats = await extract_cookies(accounts, status, uid, cancel_flag)
    if stats.get('cancelled'):
        funny = random.choice(FUNNY_CANCEL); await status.edit_text(f"❌ *Cancelled!*\n\n{funny}\n\nGot: {stats['login_success']} cookies\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download Cookies", callback_data="dl_cookies")], [InlineKeyboardButton("🏠 Home", callback_data="go_home")]])); context.user_data['last_stats'] = stats; await update.message.reply_text("👇 Choose:", reply_markup=main_kb()); return MENU

    push_r = None; push_ok = push_fail = push_dup = 0; job_id = "N/A"; api_off = False
    if stats['cookie_results']:
        try: await status.edit_text(f"⚡ Got cookies: {stats['login_success']} items! ✅\n{random.choice(FUNNY_PUSH_WAIT)}")
        except Exception: pass
        push_list = [{'converted': f"{r['username']}:{r['password']}|||{r['cookie_string']}||", 'username': r['username']} for r in stats['cookie_results']]
        push_r = await browser_push(push_list)
        if push_r.get('success'): push_ok = push_r.get('server_success', 0); push_fail = push_r.get('server_failed', 0); push_dup = max(0, push_r.get('already_submitted', 0)); job_id = push_r.get('job_id', 'N/A')
        elif push_r.get('api_offline') or push_r.get('push_locked'): api_off = True
    update_stats(uid, stats['login_success'], push_ok, stats['login_failed'])
    if uid in user_db: user_db[uid]['total_push'] += stats['login_success']; user_db[uid]['total_success'] += push_ok; user_db[uid]['total_failed'] += stats['login_failed']
    bar = get_bar(stats['total'], stats['total']); funny = random.choice(FUNNY_COMPLETE)
    if api_off:
        off_msg = random.choice(FUNNY_API_DEAD); summary = f"╔══════════════════════════╗\n  😴⛔ Server Sleeping ⛔😴  \n╚══════════════════════════╝\n\n{off_msg}\n\n┌─── 🍪 Cookie Report ─────┐\n│ 📌 Total   : {stats['total']:>4}          │\n│ ✅ Success : {stats['login_success']:>4}          │\n│ ❌ Failed  : {stats['login_failed']:>4}          │\n└──────────────────────────┘\n\n💾 Download cookies!\nLater push via *ONLY PUSH*\n\n_{DEV_TAG}_"
    else:
        summary = f"╔══════════════════════════╗\n  ✅🎉 {funny} 🎉✅  \n╚══════════════════════════╝\n\n📊 {bar} 100%\n\n┌─── 🍪 Cookie Report ─────┐\n│ 📌 Total   : {stats['total']:>4}          │\n│ ✅ Success : {stats['login_success']:>4}          │\n│ ❌ Failed  : {stats['login_failed']:>4}          │\n└──────────────────────────┘\n\n┌─── ⚡ Push Report ────────┐\n│ ✅ Success : {push_ok:>4}          │\n│ ❌ Failed  : {push_fail:>4}          │\n│ ⚠️ Already : {push_dup:>4}          │\n│ 📋 Job ID : {str(job_id)[:14]:<14}  │\n└──────────────────────────┘\n\n_{DEV_TAG}_"
    btns = [[InlineKeyboardButton("📥 Download Cookies (.txt)", callback_data="dl_cookies")], [InlineKeyboardButton(f"📋 Failed List ({stats['login_failed']})", callback_data="dl_failed")], [InlineKeyboardButton(f"🔄 Retry ({stats['login_failed']})", callback_data="retry_failed")]]
    await status.edit_text(summary, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(btns)); await update.message.reply_text("👇 Choose:", reply_markup=main_kb()); await send_admin_log(context, uid, tg_user, full_name, stats, push_r)
    context.user_data['last_stats'] = stats; context.user_data['last_push'] = push_r; context.user_data['retry_accounts'] = stats['retry_accounts']; context.user_data['tg_user'] = tg_user; context.user_data['full_name'] = full_name; return MENU

# =============================================================
# ⚡ ONLY PUSH
# =============================================================
async def op_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['mode'] = 'op'; await update.message.reply_text(f"{random.choice(FUNNY_OP_ASK)}\n\n📌 Format:\n`username|password|cookie`", parse_mode='Markdown', reply_markup=cancel_kb_reply()); return OP_DATA

async def op_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.strip() == "❌ বাতিল করো": return await do_cancel(update, context)
    uid = update.effective_user.id; tg_user = update.effective_user.username or f"ID_{uid}"; full_name = (f"{update.effective_user.first_name or ''} {update.effective_user.last_name or ''}").strip()
    c = ""
    if update.message.document:
        try: f = await update.message.document.get_file(); c = (await f.download_as_bytearray()).decode('utf-8', errors='replace')
        except Exception as e: await update.message.reply_text(f"❌ File error: {e}", reply_markup=cancel_kb_reply()); return OP_DATA
    elif update.message.text: c = update.message.text
    if not c.strip(): await update.message.reply_text("❌ Empty! 😤", reply_markup=cancel_kb_reply()); return OP_DATA
    lines = [l.strip() for l in c.split('\n') if l.strip()]; conv, fail = [], []
    for idx, line in enumerate(lines, 1):
        parts = line.split('|')
        if len(parts) >= 3:
            u = parts[0].strip(); p = parts[1].strip(); ck = '|'.join(parts[2:]).strip()
            if u and p and ck and '=' in ck: conv.append({'converted': f"{u}:{p}|||{ck}||", 'username': u})
            else: fail.append({'line': idx, 'username': u or line, 'reason': 'Invalid'})
        else: fail.append({'line': idx, 'username': line, 'reason': 'Format wrong'})
    if not conv: await update.message.reply_text("❌ *No valid data found!*\nFormat: `username|password|cookie`", parse_mode='Markdown', reply_markup=cancel_kb_reply()); return OP_DATA
    if len(conv) > MAX_ACCOUNTS: await update.message.reply_text(f"{random.choice(FUNNY_LIMIT)}\nTaking first *100*!", parse_mode='Markdown'); conv = conv[:MAX_ACCOUNTS]
    total = len(conv) + len(fail)
    status = await update.message.reply_text(f"╔══════════════════════════╗\n  ⚡🚀 Pushing Data 🚀⚡    \n╚══════════════════════════╝\n\n📊 Total: {total} | ✅ Valid: {len(conv)} | 🚫 Invalid: {len(fail)}\n\n{random.choice(FUNNY_PUSH_WAIT)}")
    r = await browser_push(conv); home_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="go_home")]])
    if r.get('push_locked'): await status.edit_text(f"⛔ *Orders Closed!* Come tomorrow! 🙏\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=home_btn); await update.message.reply_text("👇", reply_markup=main_kb()); return MENU
    if r.get('api_offline'): off = random.choice(FUNNY_API_DEAD); await status.edit_text(f"😴 *Server Sleeping!*\n\n{off}\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=home_btn); await update.message.reply_text("👇", reply_markup=main_kb()); return MENU
    if r.get('error') == "ALREADY_SUBMITTED": await status.edit_text(f"⚠️ *Already submitted!* 🤦\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=home_btn); await update.message.reply_text("👇", reply_markup=main_kb()); return MENU
    if not r['success']: await status.edit_text(f"❌ *Push Failed!*\nReason: `{r.get('error','?')}`\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=home_btn); await update.message.reply_text("👇", reply_markup=main_kb()); return MENU
    ss = r.get('server_success', 0); sf = r.get('server_failed', 0); dup = max(0, r.get('already_submitted', 0)); jid = r.get('job_id', 'N/A'); bar = get_bar(ss, len(conv)); funny = random.choice(FUNNY_COMPLETE)
    summary = f"╔══════════════════════════╗\n  ✅⚡ {funny} ⚡✅   \n╚══════════════════════════╝\n\n📊 {bar}\n\n┌─── ⚡ Push Report ────────┐\n│ 📌 Total     : {total:>4}          │\n│ ✅ Success   : {ss:>4}          │\n│ ❌ Failed    : {sf:>4}          │\n│ ⚠️ Already   : {dup:>4}          │\n│ 🚫 Bad Format: {len(fail):>3}          │\n└──────────────────────────┘\n📋 Job ID: `{jid}`\n\n_{DEV_TAG}_"
    await status.edit_text(summary, parse_mode='Markdown', reply_markup=home_btn); await update.message.reply_text("👇 Choose!", reply_markup=main_kb())
    if uid in user_db: user_db[uid]['total_push'] += len(conv); user_db[uid]['total_success'] += ss; user_db[uid]['total_failed'] += sf
    update_stats(uid, len(conv), ss, sf)
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); out = io.StringIO(); w = csv.writer(out); w.writerow(['Date', 'Time', 'Telegram', 'Name', 'ID', 'Account', 'Status'])
        for item in conv: w.writerow([datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), f"@{tg_user}", full_name, uid, item['username'], 'Pushed'])
        data = out.getvalue().encode('utf-8')
        await context.bot.send_document(chat_id=ADMIN_LOG_CHAT_ID, document=io.BytesIO(data), filename=f"push_{tg_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", caption=f"⚡Push\n📅{now}\n👤@{tg_user}\n✅{ss} ❌{sf}\n📋{jid}")
    except Exception as e: logger.error(f"Admin log error: {e}")
    return MENU

# =============================================================
# 🔘 Menu & Callbacks
# =============================================================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = (update.message.text or "").strip()
    if t == "🍪 COOKIES + PUSH": return await cp_start(update, context)
    elif t == "⚡ ONLY PUSH": return await op_start(update, context)
    elif t == "❌ বাতিল করো": return await do_cancel(update, context)
    await update.message.reply_text("👇 Choose below:", reply_markup=main_kb()); return MENU

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query; await q.answer(); d = q.data; uid = q.from_user.id
    if d == "cancel_op": return await do_cancel(update, context)
    if d == "go_home": context.user_data.clear(); await q.message.reply_text("🏠 *Main Menu*\n👇 Choose below:", parse_mode='Markdown', reply_markup=main_kb()); return MENU
    if d == "dl_cookies":
        s = context.user_data.get('last_stats')
        if not s or not s.get('cookie_results'): await q.message.reply_text("❌ No cookies! 🤷"); return MENU
        await send_cookie_file(context, uid, s); return MENU
    if d == "dl_failed":
        s = context.user_data.get('last_stats')
        if not s or not s.get('retry_accounts'): await q.message.reply_text("❌ No failures! All successful! 🎉"); return MENU
        await send_failed_csv(context, uid, s); return MENU
    if d == "retry_failed":
        rl = context.user_data.get('retry_accounts', [])
        if not rl: await q.message.reply_text("❌ Nothing to retry! 🤷"); return MENU
        tg_user = context.user_data.get('tg_user', f"ID_{uid}"); full_name = context.user_data.get('full_name', ''); cancel_flag = {'cancelled': False}; context.user_data['cancel_flag'] = cancel_flag
        status = await q.message.reply_text(f"╔══════════════════════════╗\n  🔄✨ Retrying... ✨🔄  \n╚══════════════════════════╝\n\n📊 Total: {len(rl)} | ⚡ Running...", reply_markup=cancel_kb())
        accs = [{'username': r['username'], 'password': r['password'], 'two_fa': r.get('two_fa', 'NO')} for r in rl]
        stats = await extract_cookies(accs, status, uid, cancel_flag)
        if stats.get('cancelled'):
            funny = random.choice(FUNNY_CANCEL); await status.edit_text(f"❌ *Cancelled!*\n\n{funny}\n\nCookies had: {stats['login_success']}\n\n_{DEV_TAG}_", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download", callback_data="dl_cookies")], [InlineKeyboardButton("🏠 Home", callback_data="go_home")]])); context.user_data['last_stats'] = stats; return MENU
        push_r = None; push_ok = push_fail = push_dup = 0; job_id = "N/A"; api_off = False
        if stats['cookie_results']:
            try: await status.edit_text(f"⚡ Cookies: {stats['login_success']}✅\n{random.choice(FUNNY_PUSH_WAIT)}")
            except Exception: pass
            pl = [{'converted': f"{r['username']}:{r['password']}|||{r['cookie_string']}||", 'username': r['username']} for r in stats['cookie_results']]
            push_r = await browser_push(pl)
            if push_r.get('success'): push_ok = push_r.get('server_success', 0); push_fail = push_r.get('server_failed', 0); push_dup = max(0, push_r.get('already_submitted', 0)); job_id = push_r.get('job_id', 'N/A')
            elif push_r.get('api_offline') or push_r.get('push_locked'): api_off = True
        update_stats(uid, stats['login_success'], push_ok, stats['login_failed']); bar = get_bar(stats['total'], stats['total']); funny = random.choice(FUNNY_COMPLETE)
        if api_off: off = random.choice(FUNNY_API_DEAD); summary = f"😴 *Server Sleeping!*\n\n{off}\n\nCookies: ✅{stats['login_success']} | ❌{stats['login_failed']}\n💾 Download cookies!\n\n_{DEV_TAG}_"
        else: summary = f"╔══════════════════════════╗\n  ✅🔄 {funny} 🔄✅  \n╚══════════════════════════╝\n\n📊 {bar} 100%\n\n🍪 Cookies: ✅{stats['login_success']} | ❌{stats['login_failed']}\n⚡ Push: ✅{push_ok} | ❌{push_fail} | ⚠️{push_dup}\n\n_{DEV_TAG}_"
        btns = [[InlineKeyboardButton("📥 Download", callback_data="dl_cookies")]]
        if stats.get('retry_accounts'): context.user_data['retry_accounts'] = stats['retry_accounts']; btns.append([InlineKeyboardButton(f"📋 Failures ({stats['login_failed']})", callback_data="dl_failed")]); btns.append([InlineKeyboardButton(f"🔄 Retry ({stats['login_failed']})", callback_data="retry_failed")])
        btns.append([InlineKeyboardButton("🏠 Home", callback_data="go_home")])
        context.user_data['last_stats'] = stats; await status.edit_text(summary, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(btns)); await send_admin_log(context, uid, tg_user, full_name, stats, push_r); return MENU
    return MENU

# =============================================================
# 👑 Admin Commands
# =============================================================
def is_admin(uid): return uid in ADMIN_IDS

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): await update.message.reply_text("⛔ Permission denied!"); return
    st = "🟢 Online" if api_status_cache.get('online') else "🔴 Offline"; tp = daily_stats['total_push']; ts = daily_stats['total_success']; rate = f"{(ts/tp*100):.1f}%" if tp > 0 else "0%"
    await update.message.reply_text(f"╔══════════════════════════╗\n  👑 Admin Panel 👑       \n╚══════════════════════════╝\n\n👥 Users   : {len(user_db)}\n📤 Today   : {tp}\n✅ Success : {ts} ({rate})\n❌ Failed  : {daily_stats['total_failed']}\n🌐 API     : {st}\n🚫 Blocked : {len(banned_users)}\n🕒 Time    : {now_time()}")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("/ban <user_id>")
        return
    try:
        uid = int(context.args[0])
        banned_users.add(uid)
        if uid in user_db:
            user_db[uid]['banned'] = True
        await update.message.reply_text(f"✅ Blocked: {uid}")
    except ValueError:
        await update.message.reply_text("❌ Invalid ID!")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("/unban <user_id>")
        return
    try:
        uid = int(context.args[0])
        banned_users.discard(uid)
        if uid in user_db:
            user_db[uid]['banned'] = False
        await update.message.reply_text(f"✅ Unblocked: {uid}")
    except ValueError:
        await update.message.reply_text("❌ Invalid ID!")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("/broadcast <message>"); return
    msg = ' '.join(context.args); txt = f"📢 Announcement\n━━━━━━━━━━━━\n\n{msg}\n\n_{DEV_TAG}_"; sent = 0; bad = set()
    for cid in registered_users.copy():
        try: await context.bot.send_message(chat_id=cid, text=txt, parse_mode='Markdown'); sent += 1
        except Exception: bad.add(cid)
        await asyncio.sleep(0.05)
    registered_users -= bad; await update.message.reply_text(f"✅ Sent: {sent} | ❌ Failed: {len(bad)}")

# =============================================================
# 📅 Daily Report
# =============================================================
async def daily_report(app):
    while True:
        now = datetime.now(); tmr = (now + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0); await asyncio.sleep((tmr - now).total_seconds())
        tp = daily_stats['total_push']; ts = daily_stats['total_success']; rate = f"{(ts/tp*100):.1f}%" if tp > 0 else "0%"
        r = f"📊 Daily Report — {daily_stats['date']}\n━━━━━━━━━━━━━━━━━━━━━━━━\n👥 Active: {len(daily_stats['active_users'])}\n📤 Pushes: {tp}\n✅ Success: {ts} ({rate})\n❌ Failed: {daily_stats['total_failed']}\n📈 Users: {len(user_db)}"
        try: await app.bot.send_message(chat_id=ADMIN_LOG_CHAT_ID, text=r)
        except Exception as e: logger.error(f"Report error: {e}")
        daily_stats.update({'total_push': 0, 'total_success': 0, 'total_failed': 0, 'active_users': set(), 'date': datetime.now().strftime("%Y-%m-%d")})

# =============================================================
# 🚀 Startup & Shutdown
# =============================================================
async def post_init(app):
    health = await push_engine.health_check()
    print(f"[SYSTEM] Push Engine Status: {'ONLINE ✅' if health['online'] else 'OFFLINE ❌'} | Latency: {health['latency_ms']}ms")
    asyncio.create_task(check_api_live(app)); asyncio.create_task(daily_report(app))
    logger.info("✅ Bot Ready (Termux Mode - CF Bypass & Strict Endpoint Lock Active)")

async def post_shutdown(app):
    await push_engine.close(); logger.info("Shutdown complete.")

# =============================================================
# 🎯 Main Entry Point - Token Save/Load System
# =============================================================
def get_bot_token():
    print("\n" + "="*52); print("  ⚡💎 HBX COOKIE CONVERTER & PUSH BOT 💎⚡"); print(f"  {DEV_TAG}"); print("="*52); print()
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f: token = f.read().strip()
            if token and ":" in token: print(f"✅ Saved token found in {TOKEN_FILE}!"); print("🚀 Starting bot with saved token...\n"); return token
            else: print("⚠️ Token file exists but token is invalid!"); os.remove(TOKEN_FILE)
        except Exception as e: print(f"⚠️ Error reading token file: {e}")
    while True:
        try:
            token = input("🤖 Enter Bot Token: ").strip()
            if not token: print("❌ Cannot be empty! Try again!"); continue
            if ":" not in token or len(token) < 30: print("❌ Invalid token format! Try again!"); continue
            try:
                with open(TOKEN_FILE, 'w') as f: f.write(token)
                print(f"\n✅ Token saved to {TOKEN_FILE}!"); print("🔄 Next time you won't need to enter it again!")
            except Exception as e: print(f"⚠️ Could not save token: {e}")
            print("🚀 Starting bot...\n"); return token
        except KeyboardInterrupt: print("\n\n👋 Goodbye!"); exit(0)

def main():
    bot_token = get_bot_token()
    app = Application.builder().token(bot_token).concurrent_updates(True).post_init(post_init).post_shutdown(post_shutdown).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.Regex("^(🍪 COOKIES \\+ PUSH|⚡ ONLY PUSH)$"), menu_handler), CallbackQueryHandler(callbacks, pattern="^(go_home|dl_cookies|dl_failed|retry_failed|cancel_op)$")],
            CP_USERNAMES: [MessageHandler(filters.TEXT | filters.Document.FileExtension("txt"), cp_usernames), CallbackQueryHandler(lambda u, c: do_cancel(u, c), pattern="^cancel_op$")],
            CP_PASS_TYPE: [CallbackQueryHandler(cp_pass_type, pattern="^(pass_same|pass_diff|cancel_op)$")],
            CP_SAME_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, cp_same), CallbackQueryHandler(lambda u, c: do_cancel(u, c), pattern="^cancel_op$")],
            CP_DIFF_PASS: [MessageHandler(filters.TEXT | filters.Document.FileExtension("txt"), cp_diff), CallbackQueryHandler(lambda u, c: do_cancel(u, c), pattern="^cancel_op$")],
            CP_2FA: [MessageHandler(filters.TEXT | filters.Document.FileExtension("txt"), cp_2fa), CallbackQueryHandler(lambda u, c: do_cancel(u, c), pattern="^cancel_op$")],
            OP_DATA: [MessageHandler(filters.TEXT | filters.Document.FileExtension("txt"), op_data), CallbackQueryHandler(lambda u, c: do_cancel(u, c), pattern="^cancel_op$")],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(lambda u, c: do_cancel(u, c), pattern="^cancel_op$"), CallbackQueryHandler(callbacks, pattern="^go_home$")],
        allow_reentry=True,
        per_message=True,  # <--- এই লাইনটা True করা হয়েছে ওয়ার্নিং দূর করতে
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    
    cf_status = "Active ✅" if CURL_CFFI_AVAILABLE else "Inactive ❌ (Run: pkg install libcurl)"
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print(f"🔒 Endpoint Lock: http://skysysx.net/e/thanatos")
    print(f"🛡️ CF Bypass: {cf_status}")
    print("="*52)
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()