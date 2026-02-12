import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import pandas as pd

# File paths
USERS_FILE = os.path.join(Config.DATA_FOLDER, 'users.json')
SEARCH_LOGS_FILE = os.path.join(Config.DATA_FOLDER, 'search_logs.csv')
MESSAGES_FILE = os.path.join(Config.DATA_FOLDER, 'messages.json')

def _ensure_files_exist():
    """Ensure all required files exist with proper structure"""
    # Users file
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
    
    # Search logs file
    if not os.path.exists(SEARCH_LOGS_FILE):
        with open(SEARCH_LOGS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'user_id', 'app_id', 'country', 'app_name'])
    
    # Messages file
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump([], f)

# Initialize files on import
_ensure_files_exist()

# User Management
def load_users() -> List[Dict]:
    """Load all users from JSON file"""
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        return users if isinstance(users, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_users(users: List[Dict]) -> bool:
    """Save users to JSON file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    users = load_users()
    for user in users:
        if user.get('id') == user_id:
            return user
    return None

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    users = load_users()
    for user in users:
        if user.get('username') == username:
            return user
    return None

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    users = load_users()
    for user in users:
        if user.get('email') == email:
            return user
    return None

def create_user(username: str, email: str, password: str, is_admin: bool = False) -> Optional[Dict]:
    """Create a new user"""
    users = load_users()
    
    # Check if username or email already exists
    if get_user_by_username(username):
        return None
    if get_user_by_email(email):
        return None
    
    # Generate new user ID
    user_id = max([user.get('id', 0) for user in users], default=0) + 1
    
    # Create user object
    user = {
        'id': user_id,
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'is_admin': is_admin,
        # Mark whether this user is the main/original admin. Only set True
        # when creating the first admin in the system.
        'is_main_admin': False,
        'is_verified': False,
        'disabled': False,
        'email_sent_today': 0,
        'email_sent_total': 0,
        'last_email_sent_date': None,
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }
    
    users.append(user)
    # If creating an admin and no main admin exists yet, mark this one as main
    try:
        if is_admin:
            existing_main = any(u.get('is_main_admin') for u in users if u.get('is_admin'))
            if not existing_main:
                for u in users:
                    if u.get('id') == user_id:
                        u['is_main_admin'] = True
                        break
    except Exception:
        pass

    if save_users(users):
        return user
    return None

def verify_user(username: str, password: str) -> Optional[Dict]:
    """Verify user credentials"""
    user = get_user_by_username(username)
    if not user:
        return None
    
    if check_password_hash(user['password_hash'], password):
        return user
    return None

def update_user_last_login(user_id: int) -> bool:
    """Update user's last login timestamp"""
    users = load_users()
    for user in users:
        if user.get('id') == user_id:
            user['last_login'] = datetime.now().isoformat()
            return save_users(users)
    return False

def change_user_password(user_id: int, new_password: str) -> bool:
    """Change user password"""
    users = load_users()
    for user in users:
        if user.get('id') == user_id:
            user['password_hash'] = generate_password_hash(new_password)
            return save_users(users)
    return False

# Search Logs
def append_search_log(user_id: Optional[int], app_id: str, country: str, app_name: str = "") -> bool:
    """Append a search log entry"""
    try:
        with open(SEARCH_LOGS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                user_id if user_id is not None else "anonymous",
                app_id,
                country,
                app_name[:100]  # Truncate long names
            ])
        return True
    except Exception as e:
        print(f"Error logging search: {e}")
        return False

def get_search_logs(limit: int = 1000) -> List[Dict]:
    """Get search logs as dictionaries"""
    try:
        df = pd.read_csv(SEARCH_LOGS_FILE)
        return df.tail(limit).to_dict('records')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return []

def get_top_searched_apps(limit: int = 10) -> List[Dict]:
    """Get most frequently searched apps"""
    try:
        df = pd.read_csv(SEARCH_LOGS_FILE)
        if df.empty:
            return []
        
        top_apps = df['app_name'].value_counts().head(limit).reset_index()
        top_apps.columns = ['app_name', 'search_count']
        return top_apps.to_dict('records')
    except Exception:
        return []

def get_top_countries(limit: int = 10) -> List[Dict]:
    """Get most frequently used countries in searches"""
    try:
        df = pd.read_csv(SEARCH_LOGS_FILE)
        if df.empty:
            return []
        
        top_countries = df['country'].value_counts().head(limit).reset_index()
        top_countries.columns = ['country', 'search_count']
        return top_countries.to_dict('records')
    except Exception:
        return []

# Analysis Results
def save_result(user_id: int, result_data: Dict) -> bool:
    """Save analysis result for a user"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{user_id}_{timestamp}_{result_data.get('app_id', 'unknown')}.json"
        filepath = os.path.join(Config.RESULTS_FOLDER, filename)
        
        # Add metadata
        result_data['saved_at'] = datetime.now().isoformat()
        result_data['user_id'] = user_id
        
        with open(filepath, 'w') as f:
            json.dump(result_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving result: {e}")
        return False

def get_user_results(user_id: int, limit: int = 50) -> List[Dict]:
    """Get saved results for a user"""
    try:
        results = []
        for filename in os.listdir(Config.RESULTS_FOLDER):
            if filename.startswith(f"{user_id}_"):
                filepath = os.path.join(Config.RESULTS_FOLDER, filename)
                try:
                    with open(filepath, 'r') as f:
                        result = json.load(f)
                        results.append(result)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        
        # Sort by saved_at date, newest first
        results.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
        return results[:limit]
    except FileNotFoundError:
        return []

def get_all_results(limit: int = 100) -> List[Dict]:
    """Get all saved results (for admin)"""
    try:
        all_results = []
        for filename in os.listdir(Config.RESULTS_FOLDER):
            if filename.endswith('.json'):
                filepath = os.path.join(Config.RESULTS_FOLDER, filename)
                try:
                    with open(filepath, 'r') as f:
                        result = json.load(f)
                        all_results.append(result)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        
        # Sort by saved_at date, newest first
        all_results.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
        return all_results[:limit]
    except FileNotFoundError:
        return []

# Messages
def load_messages() -> List[Dict]:
    """Load all messages"""
    try:
        with open(MESSAGES_FILE, 'r') as f:
            messages = json.load(f)
        return messages if isinstance(messages, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_messages(messages: List[Dict]) -> bool:
    """Save messages to file"""
    try:
        with open(MESSAGES_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving messages: {e}")
        return False

def add_message(user_id: int, content: str, is_from_admin: bool = False, admin_id: Optional[int] = None) -> Optional[Dict]:
    """Add a new message"""
    messages = load_messages()
    
    # Generate message ID
    message_id = max([msg.get('id', 0) for msg in messages], default=0) + 1
    
    message = {
        'id': message_id,
        'user_id': user_id,
        'admin_id': admin_id,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'is_from_admin': is_from_admin,
        'is_read': False
    }
    
    messages.append(message)
    if save_messages(messages):
        return message
    return None

def get_user_messages(user_id: int, limit: int = 50) -> List[Dict]:
    """Get messages for a specific user"""
    messages = load_messages()
    user_messages = [msg for msg in messages if msg.get('user_id') == user_id]
    user_messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return user_messages[:limit]

def mark_message_as_read(message_id: int) -> bool:
    """Mark a message as read"""
    messages = load_messages()
    for message in messages:
        if message.get('id') == message_id:
            message['is_read'] = True
            return save_messages(messages)
    return False

def mark_message_as_unread(message_id: int) -> bool:
    """Mark a message as unread"""
    messages = load_messages()
    for message in messages:
        if message.get('id') == message_id:
            message['is_read'] = False
            return save_messages(messages)
    return False

def delete_message(message_id: int) -> bool:
    """Delete a message by ID"""
    messages = load_messages()
    new_messages = [m for m in messages if m.get('id') != message_id]
    if len(new_messages) == len(messages):
        return False
    return save_messages(new_messages)

def get_unread_message_count(user_id: int) -> int:
    """Count unread messages for a user"""
    messages = load_messages()
    user_messages = [msg for msg in messages if msg.get('user_id') == user_id and not msg.get('is_read', False)]
    return len(user_messages)

# Admin functions
def get_all_users() -> List[Dict]:
    """Get all users (without password hashes for security)"""
    users = load_users()
    # Remove password hashes for security
    for user in users:
        if 'password_hash' in user:
            del user['password_hash']
    return users

def set_user_disabled(user_id: int, disabled: bool) -> bool:
    """Set a user's disabled flag"""
    users = load_users()
    changed = False
    for user in users:
        if user.get('id') == user_id:
            user['disabled'] = bool(disabled)
            changed = True
            break
    if changed:
        return save_users(users)
    return False

def set_user_admin(user_id: int, is_admin: bool) -> bool:
    """Set or unset a user's admin flag"""
    users = load_users()
    changed = False
    for user in users:
        if user.get('id') == user_id:
            user['is_admin'] = bool(is_admin)
            changed = True
            break
    if changed:
        return save_users(users)
    return False

def set_user_verified(user_id: int, verified: bool) -> bool:
    """Mark a user as verified (manual admin approval)"""
    users = load_users()
    changed = False
    for user in users:
        if user.get('id') == user_id:
            user['is_verified'] = bool(verified)
            changed = True
            break
    if changed:
        return save_users(users)
    return False


def can_user_send_email(user_id: int) -> bool:
    """Check whether the given user can send an email report based on quotas.

    - Verified users: up to 10 emails per day.
    - Unverified users: up to 50 total emails until verified by admin.
    """
    users = load_users()
    for user in users:
        if user.get('id') == user_id:
            # Ensure counters exist
            email_today = int(user.get('email_sent_today', 0) or 0)
            email_total = int(user.get('email_sent_total', 0) or 0)
            is_verified = bool(user.get('is_verified', False))
            from datetime import datetime
            last_date = user.get('last_email_sent_date')
            today = datetime.now().date().isoformat()
            # If last sent date is different from today, treat today's count as 0
            if last_date != today:
                email_today = 0
            if is_verified:
                return email_today < 10
            else:
                return email_total < 50
    return False


def increment_user_email_counters(user_id: int) -> bool:
    """Increment email counters for a user. Resets daily counter when date changes."""
    users = load_users()
    changed = False
    from datetime import datetime
    today = datetime.now().date().isoformat()
    for user in users:
        if user.get('id') == user_id:
            last_date = user.get('last_email_sent_date')
            if last_date != today:
                user['email_sent_today'] = 0
            user['email_sent_today'] = int(user.get('email_sent_today', 0) or 0) + 1
            user['email_sent_total'] = int(user.get('email_sent_total', 0) or 0) + 1
            user['last_email_sent_date'] = today
            changed = True
            break
    if changed:
        return save_users(users)
    return False

def get_online_users(window_minutes: int = 5) -> List[Dict]:
    """Return users with last_login within the past `window_minutes` minutes"""
    users = load_users()
    online = []
    try:
        now = datetime.now()
        for user in users:
            last = user.get('last_login')
            if last:
                try:
                    last_dt = datetime.fromisoformat(last)
                    diff = now - last_dt
                    if diff.total_seconds() <= window_minutes * 60:
                        user_copy = user.copy()
                        if 'password_hash' in user_copy:
                            del user_copy['password_hash']
                        online.append(user_copy)
                except Exception:
                    continue
    except Exception:
        return []
    return online

def reset_user_password(user_id: int, new_password: str) -> bool:
    """Reset a user's password (admin function)"""
    users = load_users()
    for user in users:
        if user.get('id') == user_id:
            user['password_hash'] = generate_password_hash(new_password)
            return save_users(users)
    return False

def delete_user(user_id: int) -> bool:
    """Delete a user (admin function)"""
    users = load_users()
    users = [user for user in users if user.get('id') != user_id]
    return save_users(users)


def get_main_admin() -> Optional[Dict]:
    """Return the main admin user. If none marked, pick the earliest admin and mark it.

    This guarantees there is always a main admin set when admins exist.
    """
    users = load_users()
    # Prefer already-marked main admin
    for u in users:
        if u.get('is_admin') and u.get('is_main_admin'):
            return u

    # No explicit main admin set — pick earliest admin (by created_at or id)
    admins = [u for u in users if u.get('is_admin')]
    if not admins:
        return None

    # Try created_at ordering
    try:
        admins_sorted = sorted(admins, key=lambda x: x.get('created_at') or '')
        main = admins_sorted[0]
    except Exception:
        main = sorted(admins, key=lambda x: x.get('id', 0))[0]

    # Persist the choice
    try:
        for u in users:
            if u.get('id') == main.get('id'):
                u['is_main_admin'] = True
            else:
                # ensure others are not marked
                if u.get('is_main_admin'):
                    u['is_main_admin'] = False
        save_users(users)
    except Exception:
        pass

    return main


def set_main_admin(user_id: int) -> bool:
    """Explicitly set the main admin by user id."""
    users = load_users()
    changed = False
    for u in users:
        if u.get('id') == user_id:
            u['is_main_admin'] = True
            changed = True
        else:
            if u.get('is_main_admin'):
                u['is_main_admin'] = False
                changed = True
    if changed:
        return save_users(users)
    return False