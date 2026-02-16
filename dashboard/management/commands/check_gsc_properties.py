"""
Management command to check which GSC properties are connected for a user

Usage:
    python manage.py check_gsc_properties --email=user@example.com
    python manage.py check_gsc_properties --all
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from dashboard.models import GSCConnection
import json


class Command(BaseCommand):
    help = 'Check which Google Search Console properties are connected for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email to check properties for',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all GSC connections',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        show_all = options.get('all', False)
        
        try:
            if email:
                user = User.objects.get(email=email)
                connections = GSCConnection.objects.filter(user=user)
                self.stdout.write(f'\n📧 User: {email}')
            else:
                connections = GSCConnection.objects.all()
                if not show_all:
                    self.stdout.write(self.style.ERROR('Please specify --email or --all'))
                    return
                self.stdout.write(f'\n📧 Showing ALL GSC Connections')
            
            if not connections.exists():
                self.stdout.write(self.style.WARNING('No GSC connections found'))
                return
            
            for connection in connections:
                self.stdout.write('\n' + '='*80)
                self.stdout.write(f'User: {connection.user.email}')
                self.stdout.write(f'Status: {"🟢 Active" if connection.is_active else "🔴 Inactive"}')
                self.stdout.write(f'Connected at: {connection.connected_at.strftime("%Y-%m-%d %H:%M:%S")}')
                
                properties = connection.properties
                if isinstance(properties, str):
                    try:
                        properties = json.loads(properties)
                    except:
                        properties = [properties]
                
                self.stdout.write(f'\n📦 Properties ({len(properties)}):')
                for i, prop in enumerate(properties, 1):
                    self.stdout.write(f'  {i}. {prop}')
                
                # Check credentials
                credentials = connection.credentials
                if credentials:
                    if 'token' in credentials:
                        self.stdout.write(f'\n🔐 Credentials: Stored ✅')
                    else:
                        self.stdout.write(f'\n🔐 Credentials: Empty or invalid ❌')
                else:
                    self.stdout.write(f'\n🔐 Credentials: Not found ❌')
                
        except User.DoesNotExist:
            raise CommandError(f'User with email {email} does not exist')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write('')
