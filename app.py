from flask import Flask, render_template
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from filters import filters_bp  # Add this import
from flask_session import Session
import socket
import os
import signal
import sys
import time

# Initialize Flask extensions
login_manager = LoginManager()
mail = Mail()
server_session = Session()

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Configure session to use server-side session storage
    # This will help with cookie size issues
    app.config.update(
        SESSION_TYPE='filesystem',  # Use server-side session storage
        SESSION_PERMANENT=False,
        SESSION_USE_SIGNER=True,
        SESSION_FILE_DIR='./flask_session',
        PERMANENT_SESSION_LIFETIME=3600  # 1 hour
    )
    
    # Initialize extensions
    login_manager.init_app(app)
    mail.init_app(app)
    # Initialize server-side session (Flask-Session)
    server_session.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from auth import auth_bp
    from admin import admin_bp
    from main import main_bp
    
    app.register_blueprint(filters_bp)  # Register filters blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    
    # Configure session to use server-side session storage
    # This will help with cookie size issues
    app.config.update(
        SESSION_TYPE='filesystem',  # Use server-side session storage
        SESSION_PERMANENT=False,
        SESSION_USE_SIGNER=True,
        SESSION_FILE_DIR='./flask_session',
        PERMANENT_SESSION_LIFETIME=3600  # 1 hour
    )
    
    # Configure user loader
    @login_manager.user_loader
    def load_user(user_id):
        """Load user from file storage"""
        try:
            from file_store import get_user_by_id
            from auth import User
            
            user_dict = get_user_by_id(int(user_id))
            if user_dict:
                return User.from_dict(user_dict)
        except (ValueError, TypeError):
            pass
        return None
    # Reference to suppress "not accessed" analyzer warnings
    _ = load_user
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error=error, title='Page Not Found'), 404
    _ = not_found_error
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error=error, title='Internal Server Error'), 500
    _ = internal_error
    
    # Create default admin user if none exists
    from file_store import load_users, create_user
    users = load_users()
    admin_exists = any(user.get('is_admin') for user in users)
    
    if not admin_exists:
        print("Creating default admin user...")
        admin_user = create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_admin=True
        )
        if admin_user:
            print(f"Admin user created: {admin_user['username']}")
        else:
            print("Failed to create admin user")
    
    return app

def is_current_process_using_port(port):
    """Check if the current process is using the specified port"""
    import psutil
    
    current_pid = os.getpid()
    
    try:
        # Get all connections
        connections = psutil.net_connections()
        
        for conn in connections:
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                # Found a process listening on our port
                pid = conn.pid
                if pid == current_pid:
                    return True
    except (ImportError, AttributeError, psutil.Error):
        # If psutil is not available or fails, use a simpler approach
        pass
    
    return False

def kill_foreign_process_on_port(port):
    """Terminate any process using the specified port, except the current process"""
    import subprocess
    
    current_pid = os.getpid()
    
    try:
        # For Linux/Mac
        if sys.platform in ['linux', 'darwin']:
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True)
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid_str in pids:
                    if pid_str:
                        pid = int(pid_str)
                        # Don't kill our own process
                        if pid != current_pid:
                            try:
                                os.kill(pid, signal.SIGTERM)
                                print(f"Terminated foreign process {pid} on port {port}")
                                time.sleep(0.5)  # Give it time to shut down
                            except ProcessLookupError:
                                pass  # Process already dead
        
        # For Windows
        elif sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano', '|', 'findstr', f':{port}'], 
                                  shell=True, capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if f':{port}' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = int(parts[-1])
                            # Don't kill our own process
                            if pid != current_pid:
                                try:
                                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                                 capture_output=True)
                                    print(f"Terminated foreign process {pid} on port {port}")
                                    time.sleep(0.5)  # Give it time to shut down
                                except Exception:
                                    pass
    except Exception as e:
        print(f"Error while trying to kill process on port {port}: {e}")

def ensure_port_available(port):
    """Ensure port 5001 is available, killing any foreign process using it"""
    print(f"Checking port {port} availability...")
    
    # Try to bind to the port to check if it's in use
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        test_socket.bind(('0.0.0.0', port))
        test_socket.close()
        print(f"Port {port} is available.")
        return True
    except OSError as e:
        # Port is in use - check if it's us or someone else
        test_socket.close()
        
        # First, check if we're the ones using it
        if is_current_process_using_port(port):
            print(f"Port {port} is in use by this application. That's OK.")
            return True
        
        print(f"Port {port} is in use by another process. Attempting to terminate it...")
        kill_foreign_process_on_port(port)
        
        # Wait a moment and check again
        time.sleep(1)
        
        # Try binding again
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            test_socket.bind(('0.0.0.0', port))
            test_socket.close()
            print(f"Port {port} is now available after cleanup.")
            return True
        except OSError:
            print(f"Failed to free port {port}. Another process might still be using it.")
            return False

def safe_start_app(port):
    """Safely start the application with retry logic"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        if ensure_port_available(port):
            try:
                print(f"Starting application on port {port} (attempt {attempt + 1}/{max_retries})...")
                app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
                return  # App started successfully
            except OSError as e:
                print(f"Failed to start on port {port}: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                continue
        else:
            print(f"Port {port} unavailable, retrying in {retry_delay} seconds...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    print(f"Failed to start application on port {port} after {max_retries} attempts.")
    sys.exit(1)

app = create_app()

if __name__ == '__main__':
    PORT = 5001
    
    # Try to import psutil for better process detection
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
        print("Note: Install 'psutil' for better process management: pip install psutil")
    
    # Disable Flask's reloader since it causes issues with port checking
    # We'll handle restarts differently if needed
    print("Starting with debug mode but without auto-reloader to avoid port conflicts...")
    
    safe_start_app(PORT)