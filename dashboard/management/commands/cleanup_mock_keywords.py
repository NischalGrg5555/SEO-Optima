"""
Management command to delete all mock/demo keyword data from the database.
This will remove KeywordAnalysis records that were generated before GSC was properly set up.

Usage:
    python manage.py cleanup_mock_keywords
    python manage.py cleanup_mock_keywords --user=email@example.com
    python manage.py cleanup_mock_keywords --all (without confirmation)
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from dashboard.models import KeywordAnalysis


class Command(BaseCommand):
    help = 'Delete all mock/demo keyword data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Specify a user email to delete keyword data for that user only',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all without confirmation prompt',
        )

    def handle(self, *args, **options):
        user_email = options.get('user')
        delete_all = options.get('all', False)
        
        # Get keyword analyses to delete
        if user_email:
            try:
                user = User.objects.get(email=user_email)
                analyses = KeywordAnalysis.objects.filter(user=user)
            except User.DoesNotExist:
                raise CommandError(f'User with email {user_email} does not exist')
        else:
            analyses = KeywordAnalysis.objects.all()
        
        count = analyses.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No keyword analyses found to delete'))
            return
        
        self.stdout.write(f'Found {count} keyword analysis records')
        
        if user_email:
            self.stdout.write(f'User: {user_email}')
        else:
            self.stdout.write('Scope: ALL USERS')
        
        # Confirm deletion
        if not delete_all:
            confirm = input(f'\nAre you sure you want to delete {count} keyword analysis records? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Deletion cancelled'))
                return
        
        # Delete
        deleted_count, _ = analyses.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} keyword analysis records')
        )
        self.stdout.write(
            self.style.WARNING('All mock/demo keyword data has been removed from the database.')
        )
        self.stdout.write('Only real Google Search Console data will be stored going forward.')
