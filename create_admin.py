#!/usr/bin/env python3
"""Utility script to create or update the main admin user.

Usage examples:
  - Reset password for user id 1:
      python create_admin.py --id 1 --password newpass
  - Reset by username:
      python create_admin.py --username admin --password newpass
  - Create a new admin user interactively:
      python create_admin.py --create --username admin2 --email admin2@example.com --admin
"""

import argparse
import getpass
import sys
from file_store import (
    get_user_by_id, get_user_by_username, reset_user_password,
    create_user, get_all_users, set_main_admin, get_main_admin
)


def prompt_password(confirm=True):
    pw = getpass.getpass('Password: ')
    if confirm:
        pw2 = getpass.getpass('Confirm Password: ')
        if pw != pw2:
            print('Passwords do not match', file=sys.stderr)
            return None
    return pw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, help='User ID to reset password for')
    parser.add_argument('--username', help='Username to reset password for')
    parser.add_argument('--password', help='New password (if omitted, will prompt)')
    parser.add_argument('--create', action='store_true', help='Create a new user when provided')
    parser.add_argument('--email', help='Email (required when --create)')
    parser.add_argument('--admin', action='store_true', help='Create user as admin')
    parser.add_argument('--make-main', type=int, help='Set existing user id as main admin')
    parser.add_argument('--show-main', action='store_true', help='Show current main admin')

    args = parser.parse_args()

    # Show main admin
    if args.show_main:
        main = get_main_admin()
        if not main:
            print('No main admin set', file=sys.stderr)
            sys.exit(0)
        print(f"Main admin: id={main.get('id')} username={main.get('username')} email={main.get('email')}")
        return

    # Explicitly set main admin
    if args.make_main is not None:
        ok = set_main_admin(args.make_main)
        if ok:
            print(f'Successfully set user id {args.make_main} as main admin')
            sys.exit(0)
        else:
            print(f'Failed to set user id {args.make_main} as main admin', file=sys.stderr)
            sys.exit(2)

    if args.create:
        if not args.username or not args.email:
            parser.error('--create requires --username and --email')

        password = args.password or prompt_password()
        if not password:
            print('Password required', file=sys.stderr)
            sys.exit(1)

        user = create_user(args.username, args.email, password, is_admin=args.admin)
        if user:
            print(f"Created user: id={user.get('id')} username={user.get('username')} is_admin={user.get('is_admin')}")
        else:
            print('Failed to create user (username or email may already exist)', file=sys.stderr)
            sys.exit(2)

        # If created as admin and became main admin, inform user
        if args.admin:
            users = get_all_users()
            main_admins = [u for u in users if u.get('is_admin') and u.get('is_main_admin')]
            if main_admins and any(u.get('username') == args.username for u in main_admins):
                print('This user has been marked as the main admin.')

        return

    # Not creating: must reset an existing user
    target = None
    if args.id:
        target = get_user_by_id(args.id)
    elif args.username:
        target = get_user_by_username(args.username)
    else:
        parser.error('Either --id or --username required when not using --create')

    if not target:
        print('User not found', file=sys.stderr)
        sys.exit(3)

    password = args.password or prompt_password()
    if not password:
        print('Password required', file=sys.stderr)
        sys.exit(1)

    ok = reset_user_password(target.get('id'), password)
    if ok:
        print(f"Password updated for user id={target.get('id')} username={target.get('username')}")
    else:
        print('Failed to update password', file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()
