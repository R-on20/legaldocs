#!/usr/bin/env python
"""
Test daily activity chart data directly
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from main.models import AuditLog
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate

def test_daily_activity_data():
    print("Testing daily activity chart data...")
    
    # Same logic as in the view (FIXED VERSION)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=6)  # Changed from 7 to 6 to include today
    
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    
    # Get daily activity counts
    daily_data = AuditLog.objects.filter(
        timestamp__range=[start_date, end_date]
    ).annotate(
        day=TruncDate('timestamp')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    print(f"Raw daily data: {list(daily_data)}")
    
    labels = []
    data = []
    
    # Fill in all days, even if no activity
    current_date = start_date.date()
    activity_dict = {item['day']: item['count'] for item in daily_data}
    
    print(f"Activity dict: {activity_dict}")
    
    for i in range(7):  # Still 7 days total
        day_date = current_date + timedelta(days=i)
        label = day_date.strftime('%a %m/%d')  # Mon 01/15
        count = activity_dict.get(day_date, 0)
        
        labels.append(label)
        data.append(count)
        
        print(f"Day {i}: {day_date} -> {label} = {count}")
    
    print(f"\nFinal result:")
    print(f"Labels: {labels}")
    print(f"Data: {data}")
    
    # Also check total audit logs
    total_logs = AuditLog.objects.count()
    recent_logs = AuditLog.objects.filter(timestamp__range=[start_date, end_date]).count()
    print(f"\nTotal audit logs: {total_logs}")
    print(f"Recent audit logs (last 7 days): {recent_logs}")
    
    # Show some recent audit logs
    print(f"\nRecent audit log examples:")
    recent_examples = AuditLog.objects.filter(
        timestamp__range=[start_date, end_date]
    ).order_by('-timestamp')[:5]
    
    for log in recent_examples:
        print(f"- {log.timestamp.strftime('%Y-%m-%d %H:%M')} {log.action} by user {log.user_id}")

if __name__ == '__main__':
    test_daily_activity_data()
