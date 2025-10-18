from imap_tools import MailBox, AND, A, OR, NOT
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import time
import sys
import signal
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
mail_host = os.getenv('MAIL_HOST', 'imap.mail.us-west-2.awsapps.com')
mail_user = os.getenv('MAIL_USER')
mail_pass = os.getenv('MAIL_PASS')
mail_source_box = os.getenv('MAIL_SOURCE_BOX', 'INBOX')
mail_destination_box = os.getenv('MAIL_DESTINATION_BOX', 'Archive')

# Validate required credentials
if not mail_user or not mail_pass:
    print("ERROR: Missing required credentials!")
    print("Please set MAIL_USER and MAIL_PASS environment variables or create a .env file.")
    print("See .env.example for reference.")
    sys.exit(1)

# Define the overall date range
start_date_string = os.getenv('START_DATE', "2022-11-05")
end_date_string = os.getenv('END_DATE', "2025-01-01")

start_date = datetime.strptime(start_date_string, "%Y-%m-%d").date()
if end_date_string != "":
    end_date = datetime.strptime(end_date_string, "%Y-%m-%d").date()
else:
    end_date = start_date + relativedelta(months=12)

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds: int):
    """Raise TimeoutException if the with-block exceeds the given number of seconds."""
    def _handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")

    previous_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)

def process_emails_in_batches(mailbox, start_datetime, end_datetime, batch_size=50):
    """Process emails in smaller batches to avoid IMAP session issues"""
    try:
        # Convert datetime to date for IMAP criteria
        start_date = start_datetime.date()
        end_date = end_datetime.date()
        
        print(f"  Searching for emails from {start_date} to {end_date}")
        
        # Get all UIDs for the time range
        uids = list(mailbox.uids(criteria=AND(date_gte=start_date, date_lt=end_date)))
        
        if not uids:
            print(f"  No emails found for {start_date} to {end_date}")
            return 0
        
        print(f"  Found {len(uids)} emails, processing in batches of {batch_size}")
        
        # Process in batches
        processed = 0
        for i in range(0, len(uids), batch_size):
            batch = uids[i:i + batch_size]
            try:
                with time_limit(300):
                    mailbox.move(batch, mail_destination_box)
                processed += len(batch)
                print(f"  Processed batch {i//batch_size + 1}: {len(batch)} emails (total: {processed})")
                
                # Small delay between batches to prevent overwhelming the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Error processing batch {i//batch_size + 1}: {e}")
                # Continue with next batch instead of failing completely
                continue
                
        return processed
        
    except Exception as e:
        print(f"  Error in process_emails_in_batches: {e}")
        return 0

def debug_inbox_emails(mailbox, sample_size=10):
    """Debug function to see what emails are actually in the inbox"""
    try:
        print(f"  DEBUG: Checking inbox for sample emails...")
        
        # Get a sample of recent emails to see their dates
        all_uids = list(mailbox.uids())
        print(f"  DEBUG: Total emails in inbox: {len(all_uids)}")
        
        if all_uids:
            # Get details for first few emails
            sample_uids = all_uids[:sample_size]
            for i, uid in enumerate(sample_uids):
                try:
                    msg = mailbox.fetch(uid)
                    for msg_data in msg:
                        print(f"  DEBUG: Email {i+1} - UID: {uid}, Date: {msg_data.date}, Subject: {msg_data.subject[:50]}...")
                        break
                except Exception as e:
                    print(f"  DEBUG: Could not fetch email {uid}: {e}")
                    
    except Exception as e:
        print(f"  DEBUG: Error checking inbox: {e}")

def safe_mailbox_operation(operation_func, *args, **kwargs):
    """Safely execute mailbox operations with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with MailBox(mail_host).login(mail_user, mail_pass, mail_source_box) as mailbox:
                return operation_func(mailbox, *args, **kwargs)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                print(f"All {max_retries} attempts failed. Moving to next time period.")
                return 0

# First, let's test the connection and see what emails are available
print("=== TESTING CONNECTION AND CHECKING FOR EMAILS ===")
def test_connection_and_emails():
    try:
        with MailBox(mail_host).login(mail_user, mail_pass, mail_source_box) as mailbox:
            print(f"Successfully connected to {mail_host}")
            
            # Get total count of emails
            all_uids = list(mailbox.uids())
            print(f"Total emails in {mail_source_box}: {len(all_uids)}")
            
            if all_uids:
                # Check a few recent emails
                print("\nSample of recent emails:")
                sample_uids = all_uids[:5]
                for i, uid in enumerate(sample_uids):
                    try:
                        msg = mailbox.fetch(uid)
                        for msg_data in msg:
                            print(f"  {i+1}. UID: {uid}, Date: {msg_data.date}, From: {msg_data.from_}, Subject: {msg_data.subject[:60]}...")
                            break
                    except Exception as e:
                        print(f"  {i+1}. UID: {uid} - Error fetching: {e}")
                
                # Test date range search
                print(f"\nTesting date range search for {start_date} to {start_date + timedelta(days=1)}")
                test_uids = list(mailbox.uids(criteria=AND(date_gte=start_date, date_lt=start_date + timedelta(days=1))))
                print(f"Emails found in date range: {len(test_uids)}")
                
    except Exception as e:
        print(f"Connection test failed: {e}")

test_connection_and_emails()
print("\n" + "="*60 + "\n")

# Process emails one month at a time
current_date = start_date
total_processed = 0

while current_date < end_date:
    # Calculate the end of the current month
    next_month = current_date + relativedelta(months=1)
    month_end = min(next_month, end_date)
    
    print(f"\n=== Processing month: {current_date} to {month_end} ===")

    # Process day by day with better debugging
    current_day = current_date
    while current_day < month_end:
        next_day = current_day + timedelta(days=1)
        
        print(f"\nProcessing day: {current_day}")
        
        # Test the date range search for this specific day
        def test_day_search(mailbox):
            print(f"  DEBUG: Testing date search for {current_day} to {next_day}")
            test_uids = list(mailbox.uids(criteria=AND(date_gte=current_day, date_lt=next_day)))
            print(f"  DEBUG: Found {len(test_uids)} emails for this day")
            
            if test_uids:
                # Show details of first few emails
                for i, uid in enumerate(test_uids[:3]):
                    try:
                        msg = mailbox.fetch(uid)
                        for msg_data in msg:
                            print(f"    Email {i+1}: UID {uid}, Date: {msg_data.date}, Subject: {msg_data.subject[:50]}...")
                            break
                    except Exception as e:
                        print(f"    Email {i+1}: UID {uid} - Error: {e}")
            
            return len(test_uids)
        
        # Test the search first
        safe_mailbox_operation(test_day_search)
        
        # Now process the emails for this day (simplified - no hour-by-hour)
        def process_day_emails(mailbox):
            print(f"  Processing emails from {current_day} to {next_day}")
            
            # Get all UIDs for this day
            uids = list(mailbox.uids(criteria=AND(date_gte=current_day, date_lt=next_day)))
            
            if not uids:
                print(f"  No emails found for {current_day}")
                return 0
            
            print(f"  Found {len(uids)} emails, processing in batches")
            
            # Process in smaller batches
            batch_size = 25
            processed = 0
            for i in range(0, len(uids), batch_size):
                batch = uids[i:i + batch_size]
                try:
                    # put a timeout of 60 seconds
                    with time_limit(60):
                        mailbox.move(batch, mail_destination_box)
                    processed += len(batch)
                    print(f"  Processed batch {i//batch_size + 1}: {len(batch)} emails (total: {processed})")
                    time.sleep(0.5)  # Small delay between batches
                except Exception as e:
                    print(f"  Error processing batch {i//batch_size + 1}: {e}")
                    continue
            
            return processed
        
        # Process emails for this day
        processed = safe_mailbox_operation(process_day_emails)
        total_processed += processed
        print(f"  Day completed: {processed} emails processed")
        
        current_day = next_day

    print(f"Month completed. Total processed so far: {total_processed}")
    current_date = next_month

print(f"\n=== ARCHIVE COMPLETE ===")
print(f"Total emails processed: {total_processed}")
 