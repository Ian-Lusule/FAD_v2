from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from file_store import (
    get_all_users, reset_user_password, delete_user,
    get_search_logs, get_top_searched_apps, get_top_countries,
    get_all_results, load_messages, save_messages, add_message,
    get_user_by_id, get_user_messages
)
from file_store import delete_message, mark_message_as_read, mark_message_as_unread, set_user_disabled, set_user_admin, set_user_verified, get_online_users
import csv
import io
from datetime import datetime
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    users = get_all_users()
    total_users = len(users)
    
    search_logs = get_search_logs(limit=1000)
    total_searches = len(search_logs)
    
    top_apps = get_top_searched_apps(limit=10)
    top_countries = get_top_countries(limit=10)
    
    recent_results = get_all_results(limit=10)
    # Normalize recent results to ensure template-safe keys
    normalized_results = []
    for r in recent_results:
        rr = dict(r) if isinstance(r, dict) else {}
        # ensure metrics dict
        metrics = rr.get('metrics') or rr.get('metrics_summary') or {}
        # if sentiment_counts exist, try to compute negative pct
        if not metrics and rr.get('sentiment_counts'):
            sc = rr.get('sentiment_counts')
            try:
                total = sum(sc.values()) if isinstance(sc, dict) else 0
                neg = sc.get('Negative', 0) if isinstance(sc, dict) else 0
                metrics = {'negative_pct': (neg / total * 100) if total else 0.0}
            except Exception:
                metrics = {'negative_pct': 0.0}
        # Ensure numeric fields exist
        if 'negative_pct' not in metrics:
            metrics['negative_pct'] = float(rr.get('negative_pct', 0.0) or 0.0)
        if 'positive_pct' not in metrics:
            metrics['positive_pct'] = float(rr.get('positive_pct', 0.0) or 0.0)
        if 'neutral_pct' not in metrics:
            metrics['neutral_pct'] = float(rr.get('neutral_pct', 0.0) or 0.0)
        if 'app_rating_score' not in metrics:
            metrics['app_rating_score'] = float(rr.get('app_rating_score', 0.0) or 0.0)
        rr['metrics'] = metrics
        # ensure other expected keys
        if 'app_name' not in rr:
            rr['app_name'] = rr.get('app_id') or rr.get('app_details', {}).get('title') if rr.get('app_details') else rr.get('app_id')
        if 'user_id' not in rr:
            rr['user_id'] = rr.get('user_id', 'unknown')
        if 'saved_at' not in rr:
            rr['saved_at'] = rr.get('saved_at', '')
        if 'risk_detected' not in rr:
            rr['risk_detected'] = rr.get('risk_detected', False)
        if 'country' not in rr:
            rr['country'] = rr.get('country', '')
        normalized_results.append(rr)
    recent_results = normalized_results
    
    # Get recent messages
    all_messages = load_messages()
    recent_messages = sorted(all_messages, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_searches=total_searches,
                         top_apps=top_apps,
                         top_countries=top_countries,
                         recent_results=recent_results,
                         recent_messages=recent_messages)

@admin_bp.route('/users')
@login_required
@admin_required
def user_management():
    """User management page"""
    users = get_all_users()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_user_password_route(user_id):
    """Reset user password"""
    if user_id == current_user.id:
        flash('You cannot reset your own password from here', 'danger')
        return redirect(url_for('admin.user_management'))
    
    new_password = request.form.get('new_password', '').strip()
    if not new_password or len(new_password) < 8:
        flash('Password must be at least 8 characters long', 'danger')
        return redirect(url_for('admin.user_management'))
    
    if reset_user_password(user_id, new_password):
        flash(f'Password reset for user ID {user_id}', 'success')
    else:
        flash('Failed to reset password', 'danger')
    
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user_route(user_id):
    """Delete a user"""
    if user_id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.user_management'))
    
    if delete_user(user_id):
        flash(f'User ID {user_id} deleted', 'success')
    else:
        flash('Failed to delete user', 'danger')
    
    return redirect(url_for('admin.user_management'))


@admin_bp.route('/users/disable/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_disabled(user_id):
    """Disable or enable a user account"""
    if user_id == current_user.id:
        flash('You cannot change your own disabled status', 'danger')
        return redirect(url_for('admin.user_management'))

    user = get_user_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.user_management'))

    new_state = not bool(user.get('disabled', False))
    if set_user_disabled(user_id, new_state):
        flash(f"User {'disabled' if new_state else 'enabled'} successfully", 'success')
    else:
        flash('Failed to update user status', 'danger')
    return redirect(url_for('admin.user_management'))


@admin_bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id):
    """Grant or revoke admin privileges for a user"""
    if user_id == current_user.id:
        flash('You cannot change your own admin status', 'danger')
        return redirect(url_for('admin.user_management'))

    user = get_user_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.user_management'))

    new_admin_state = not bool(user.get('is_admin', False))
    # Only the main/original admin may grant or revoke admin status
    try:
        from file_store import get_main_admin
        main_admin = get_main_admin()
        if not main_admin or main_admin.get('id') != current_user.id:
            flash('Only the main administrator can promote or revoke admin privileges', 'danger')
            return redirect(url_for('admin.user_management'))
    except Exception:
        # Fallback to previous behavior using current_user flag
        if not getattr(current_user, 'is_main_admin', False):
            flash('Only the main administrator can promote or revoke admin privileges', 'danger')
            return redirect(url_for('admin.user_management'))

    # Prevent removing the last admin
    if not new_admin_state:
        users = get_all_users()
        admin_count = sum(1 for u in users if u.get('is_admin'))
        if admin_count <= 1:
            flash('Cannot remove admin status from the last admin', 'danger')
            return redirect(url_for('admin.user_management'))

    # Prevent revoking the original/main admin
    if not new_admin_state and user.get('is_main_admin'):
        flash('Cannot revoke admin status from the original main admin', 'danger')
        return redirect(url_for('admin.user_management'))

    if set_user_admin(user_id, new_admin_state):
        flash(f"User {'granted' if new_admin_state else 'revoked'} admin privileges", 'success')
    else:
        flash('Failed to update admin status', 'danger')

    return redirect(url_for('admin.user_management'))

@admin_bp.route('/messages')
@login_required
@admin_required
def message_center():
    """Admin message center"""
    all_messages = load_messages()
    
    # Group messages by user
    user_messages = {}
    for message in all_messages:
        user_id = message['user_id']
        if user_id not in user_messages:
            user_info = get_user_by_id(user_id)
            user_messages[user_id] = {
                'user': user_info,
                'messages': []
            }
        user_messages[user_id]['messages'].append(message)
    
    # Sort users by most recent message
    sorted_users = sorted(user_messages.items(),
                         key=lambda x: max([msg['timestamp'] for msg in x[1]['messages']]),
                         reverse=True)
    
    return render_template('admin/messages.html', user_messages=dict(sorted_users))


@admin_bp.route('/messages/view/<int:message_id>')
@login_required
@admin_required
def view_message(message_id):
    all_messages = load_messages()
    msg = next((m for m in all_messages if m.get('id') == message_id), None)
    if not msg:
        flash('Message not found', 'danger')
        return redirect(url_for('admin.message_center'))
    return render_template('admin/view_message.html', message=msg)


@admin_bp.route('/messages/mark_read/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def admin_mark_read(message_id):
    if mark_message_as_read(message_id):
        flash('Message marked as read', 'success')
    else:
        flash('Failed to mark message', 'danger')
    return redirect(url_for('admin.message_center'))


@admin_bp.route('/messages/mark_unread/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def admin_mark_unread(message_id):
    if mark_message_as_unread(message_id):
        flash('Message marked as unread', 'success')
    else:
        flash('Failed to mark message', 'danger')
    return redirect(url_for('admin.message_center'))


@admin_bp.route('/messages/delete/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_message(message_id):
    if delete_message(message_id):
        flash('Message deleted', 'success')
    else:
        flash('Failed to delete message', 'danger')
    return redirect(url_for('admin.message_center'))


@admin_bp.route('/notify_all', methods=['POST'])
@login_required
@admin_required
def notify_all():
    content = request.form.get('content', '').strip()
    if not content:
        flash('Notification content required', 'danger')
        return redirect(url_for('admin.dashboard'))
    users = get_all_users()
    for user in users:
        add_message(user.get('id'), content, is_from_admin=True, admin_id=current_user.id)
    flash('Notification sent to all users', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/online')
@login_required
@admin_required
def users_online():
    online = get_online_users()
    return render_template('admin/online.html', online=online)


@admin_bp.route('/users/verify/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def verify_user_route(user_id):
    """Verify or unverify a user account"""
    if user_id == current_user.id:
        flash('You cannot change your own verification status', 'danger')
        return redirect(url_for('admin.user_management'))

    user = get_user_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.user_management'))

    new_state = not bool(user.get('is_verified', False))
    if set_user_verified(user_id, new_state):
        flash(f"User verification {'granted' if new_state else 'revoked'}", 'success')
    else:
        flash('Failed to update verification status', 'danger')
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/messages/send/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def send_message(user_id):
    """Send a message to a user"""
    content = request.form.get('content', '').strip()
    if not content:
        flash('Message cannot be empty', 'danger')
        return redirect(url_for('admin.message_center'))
    
    # Add message (from admin)
    if add_message(user_id, content, is_from_admin=True, admin_id=current_user.id):
        flash('Message sent successfully', 'success')
    else:
        flash('Failed to send message', 'danger')
    
    return redirect(url_for('admin.message_center'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analytics dashboard"""
    search_logs = get_search_logs(limit=5000)
    top_apps = get_top_searched_apps(limit=20)
    top_countries = get_top_countries(limit=20)
    
    # Calculate daily searches
    daily_counts = {}
    for log in search_logs:
        date = log['timestamp'][:10]  # Get YYYY-MM-DD
        daily_counts[date] = daily_counts.get(date, 0) + 1
    
    daily_data = [{'date': date, 'count': count} 
                  for date, count in sorted(daily_counts.items())]
    
    return render_template('admin/analytics.html',
                         daily_data=daily_data,
                         top_apps=top_apps,
                         top_countries=top_countries,
                         total_searches=len(search_logs))

@admin_bp.route('/export/logs')
@login_required
@admin_required
def export_logs():
    """Export search logs as CSV"""
    search_logs = get_search_logs(limit=10000)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Timestamp', 'User ID', 'App ID', 'Country', 'App Name'])
    
    # Write data
    for log in search_logs:
        writer.writerow([
            log.get('timestamp', ''),
            log.get('user_id', ''),
            log.get('app_id', ''),
            log.get('country', ''),
            log.get('app_name', '')
        ])
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'search_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@admin_bp.route('/export/users')
@login_required
@admin_required
def export_users():
    """Export users as CSV"""
    users = get_all_users()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Username', 'Email', 'Is Admin', 'Created At', 'Last Login'])
    
    # Write data
    for user in users:
        writer.writerow([
            user.get('id', ''),
            user.get('username', ''),
            user.get('email', ''),
            user.get('is_admin', False),
            user.get('created_at', ''),
            user.get('last_login', '')
        ])
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@admin_bp.route('/api/stats')
@login_required
@admin_required
def get_stats():
    """API endpoint for dashboard statistics"""
    users = get_all_users()
    search_logs = get_search_logs(limit=1000)
    
    stats = {
        'total_users': len(users),
        'total_searches': len(search_logs),
        'active_today': 0,  # Would need login tracking
        'recent_results': len(get_all_results(limit=50))
    }
    
    return jsonify(stats)