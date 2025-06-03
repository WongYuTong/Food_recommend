import os
import django
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')
django.setup()

try:
    out = StringIO()
    call_command('dumpdata', exclude=['auth.permission', 'contenttypes'], stdout=out)
    data = out.getvalue()
    with open('db_backup.json', 'w', encoding='utf-8') as f:
        f.write(data)
except CommandError as e:
    print(f"Error: {e}")
