# The IMAP Mayflower
Legal Mass Migration for Insanely Overpopulated Inboxes

A Python script to efficiently archive large volumes of emails from your IMAP inbox to a designated archive folder, processing them in manageable batches to avoid server timeouts.

## Features

- **Batch Processing**: Processes emails in small batches to prevent IMAP session timeouts
- **Date Range Processing**: Archives emails within specified date ranges
- **Error Handling**: Robust error handling with retry logic
- **Secure Credentials**: Uses environment variables for secure credential management
- **Configurable**: Easy to configure via environment variables

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit the `.env` file with your actual email credentials:

```env
# IMAP server hostname
MAIL_HOST=imap.gmail.com

# Your email address
MAIL_USER=your-email@example.com

# Your email password or app-specific password
MAIL_PASS=your-password-here

# Source mailbox (usually INBOX)
MAIL_SOURCE_BOX=INBOX

# Destination mailbox for archiving
MAIL_DESTINATION_BOX=Archive

# Date range for processing
START_DATE=2022-11-05
END_DATE=2025-01-01
```

### 3. Run the Script

```bash
python execute.py
```

## Security Notes

- **Never commit your `.env` file** - it contains sensitive credentials
- Use app-specific passwords when possible (especially for Gmail)
- The `.env` file is already included in `.gitignore` to prevent accidental commits
- Consider using environment variables directly in production environments

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `MAIL_HOST` | IMAP server hostname | Required |
| `MAIL_USER` | Your email address | Required |
| `MAIL_PASS` | Your email password | Required |
| `MAIL_SOURCE_BOX` | Source mailbox to archive from | `INBOX` |
| `MAIL_DESTINATION_BOX` | Destination archive mailbox | `Archive` |
| `START_DATE` | Start date for archiving (YYYY-MM-DD) | `2022-11-05` |
| `END_DATE` | End date for archiving (YYYY-MM-DD) | `2025-01-01` |

## How It Works

1. **Connection Test**: First tests the IMAP connection and shows sample emails
2. **Month-by-Month Processing**: Processes emails one month at a time
3. **Day-by-Day Processing**: Within each month, processes emails day by day
4. **Batch Processing**: Emails are moved in small batches (25-50 at a time) to prevent timeouts
5. **Error Recovery**: If a batch fails, the script continues with the next batch

## Troubleshooting

- **Connection Issues**: Verify your IMAP server settings and credentials
- **Timeout Errors**: The script includes timeout handling and retry logic
- **Permission Errors**: Ensure your email account has permission to move emails to the archive folder
- **Large Inboxes**: The script is designed to handle large inboxes efficiently with batch processing

## Contributing

Feel free to submit issues and enhancement requests!
