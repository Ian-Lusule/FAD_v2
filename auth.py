from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from file_store import (
    create_user, verify_user, update_user_last_login, 
    change_user_password, add_message, get_user_messages,
    get_unread_message_count
)
from config import Config
import re

auth_bp = Blueprint('auth', __name__)

class User:
    """User class for Flask-Login"""
    def __init__(self, user_dict):
        self.id = user_dict['id']
        self.username = user_dict['username']
        self.email = user_dict['email']
        self.is_admin = user_dict.get('is_admin', False)
        self.is_main_admin = user_dict.get('is_main_admin', False)
        self.password_hash = user_dict['password_hash']
    
    @staticmethod
    def from_dict(user_dict):
        return User(user_dict)
    
    def get_id(self):
        return str(self.id)
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Helper functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

# Routes
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        if not validate_email(email):
            flash('Invalid email address', 'danger')
            return render_template('auth/register.html')
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = create_user(username, email, password)
        if user:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Username or email already exists', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'true'
        
        user_dict = verify_user(username, password)
        if user_dict:
            user = User.from_dict(user_dict)
            login_user(user, remember=remember)
            update_user_last_login(user.id)
            flash('Logged in successfully!', 'success')
            
            # Redirect to next page if specified
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password:
            flash('All fields are required', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('auth/change_password.html')
        
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('auth/change_password.html')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('auth/change_password.html')
        
        # Change password
        if change_user_password(current_user.id, new_password):
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Failed to change password', 'danger')
    
    return render_template('auth/change_password.html')

@auth_bp.route('/contact_admin', methods=['GET', 'POST'])
@login_required
def contact_admin():
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        
        if not message:
            flash('Message cannot be empty', 'danger')
            return render_template('auth/contact_admin.html')
        
        # Add message (from user, not admin)
        if add_message(current_user.id, message, is_from_admin=False):
            flash('Message sent to admin successfully!', 'success')
        else:
            flash('Failed to send message', 'danger')
        
        return redirect(url_for('auth.dashboard'))
    
    return render_template('auth/contact_admin.html')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's saved results
    from file_store import get_user_results
    saved_results = get_user_results(current_user.id, limit=10)
    
    # Get unread message count
    unread_count = get_unread_message_count(current_user.id)
    
    # Get recent messages
    messages = get_user_messages(current_user.id, limit=5)
    
    return render_template('auth/dashboard.html',
                         saved_results=saved_results,
                         unread_count=unread_count,
                         messages=messages)

@auth_bp.route('/api/messages')
@login_required
def get_messages():
    """API endpoint to get user messages (JSON)"""
    messages = get_user_messages(current_user.id, limit=50)
    return jsonify({'messages': messages})

@auth_bp.route('/api/messages/read/<int:message_id>', methods=['POST'])
@login_required
def mark_message_read(message_id):
    """API endpoint to mark a message as read"""
    from file_store import mark_message_as_read
    if mark_message_as_read(message_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Message not found'}), 404