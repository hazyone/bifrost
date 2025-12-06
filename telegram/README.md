# Telegram Client

A Python library and CLI for interacting with Telegram's MTProto API (client API, not Bot API).

Built with [Telethon](https://github.com/LonamiWebs/Telethon) - a mature and well-documented Python library for the Telegram MTProto protocol.

## Features

- Full Telegram client API access (login as a user account)
- Rate limiting to respect Telegram's server limits
- Session persistence (stay logged in across restarts)
- Message history fetching with pagination
- Real-time message listening
- Export messages to JSON
- Appears as official TDesktop client

## Setup

### 1. Get API Credentials

You need API credentials from Telegram:

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Note your `api_id` and `api_hash`

Alternatively, you can use public TDesktop credentials (from the nightly build):
- API_ID: `611335`
- API_HASH: `d524b414d21f4d37f08684c1df41ac9c`

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
API_ID=611335
API_HASH=d524b414d21f4d37f08684c1df41ac9c
PHONE_NUMBER=+79991234567
TARGET_GROUP=@your_group
```

### 4. Run

```bash
python main.py
```

On first run, you'll be prompted to enter the login code sent to your Telegram account.

## Usage

### As a CLI Tool

```bash
# Run the interactive CLI
python main.py

# With environment variables (no .env file needed)
API_ID=123 API_HASH=abc PHONE_NUMBER=+1234567890 python main.py
```

### As a Library

```python
import asyncio
from config import Config
from client import TgClient

async def main():
    config = Config.from_env()
    client = TgClient(config)

    await client.connect()
    await client.login()

    # Resolve a group by username
    group = await client.resolve_group("@my_group")

    # Get last 100 messages
    messages = await client.get_messages(group, limit=100)

    for msg in messages:
        print(f"{msg.sender_name}: {msg.text}")

    # Or iterate memory-efficiently
    async for msg in client.iter_messages(group, limit=1000):
        print(f"{msg.sender_name}: {msg.text}")

    await client.disconnect()

asyncio.run(main())
```

### Joining via Invite Link

```python
# Join via invite link
group = await client.resolve_group("https://t.me/+ABC123xyz")

# Or via username
group = await client.resolve_group("@public_group")
```

## Rate Limiting

The client includes built-in rate limiting to avoid triggering Telegram's flood protection:

- Default delay between requests: 1 second
- Automatic handling of `FloodWait` errors
- Exponential backoff on errors

Configure via environment variables:

```env
FETCH_DELAY=1.0   # Delay between API calls (seconds)
BATCH_SIZE=100    # Messages per batch
```

## Security Notes

- **Never commit your `.env` file or `*.session` files**
- Session files contain authentication tokens
- Use your own API credentials from https://my.telegram.org
- This client appears as TDesktop to Telegram servers (Windows 10, version 4.16.8)

## Integration with Matrix

This tool is designed to help sync messages from Telegram to Matrix:

1. Export messages to JSON using this tool
2. Parse the JSON with your Matrix bot/bridge
3. Send to Matrix room via Matrix Client-Server API

Example exported message format:

```json
{
  "id": 12345,
  "sender_name": "John Doe",
  "sender_id": 123456789,
  "text": "Hello, world!",
  "date": "2024-01-15T10:30:00+00:00",
  "date_timestamp": 1705315800,
  "reply_to_id": null,
  "is_from_bot": false,
  "media_type": null,
  "forward_from": null
}
```

## API Reference

### TgClient

Main client class.

| Method | Description |
|--------|-------------|
| `connect()` | Connect to Telegram servers |
| `login()` | Interactive login with phone/code |
| `resolve_group(identifier)` | Resolve @username or invite link |
| `join_channel(channel)` | Join a channel/supergroup |
| `get_messages(chat, limit)` | Fetch messages with rate limiting |
| `iter_messages(chat, limit)` | Async iterator for messages |
| `listen_for_updates(chat, callback)` | Real-time message listener |
| `export_to_json(chat, path, limit)` | Export messages to JSON |

### TelegramMessage

Message data structure.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Message ID |
| `sender_name` | str | Sender's display name |
| `sender_id` | int | Sender's user ID |
| `text` | str | Message text content |
| `date` | str | ISO format datetime |
| `date_timestamp` | int | Unix timestamp |
| `reply_to_id` | int | Replied message ID |
| `is_from_bot` | bool | Is sender a bot |
| `media_type` | str | Media type if present |
| `forward_from` | str | Original sender if forwarded |

## License

MIT
