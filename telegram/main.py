#!/usr/bin/env python3
"""
Telegram Message Exporter CLI

A command-line tool for fetching messages from Telegram groups
and exporting them for use in other platforms (e.g., Matrix).
"""

import asyncio
import logging
import sys
from pathlib import Path

from config import Config
from client import TgClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Telegram Message Exporter v0.1.0")

    # Load configuration
    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(str(e))
        print("\nPlease create a .env file with your credentials.")
        print("See .env.example for reference.")
        print("Get API credentials at: https://my.telegram.org/apps")
        return 1

    # Create client
    client = TgClient(config)

    try:
        # Connect
        logger.info("Connecting to Telegram...")
        is_authorized = await client.connect()

        # Login if needed
        if not is_authorized:
            logger.info("Authentication required")
            await client.login()
        else:
            logger.info("Already authenticated")
            me = await client.client.get_me()
            logger.info(f"Logged in as: {me.first_name} (@{me.username})")

        # Get target group
        if config.target_group:
            target = config.target_group
        else:
            target = input("\nEnter group username or invite link: ").strip()

        if not target:
            logger.error("No target group specified")
            return 1

        # Resolve the group
        logger.info(f"Resolving: {target}")
        group = await client.resolve_group(target)
        title = getattr(group, "title", "Unknown")
        logger.info(f"Found: {title} (ID: {group.id})")

        # Menu
        print("\nWhat would you like to do?")
        print("1. Export messages to JSON")
        print("2. Listen for new messages (real-time)")
        print("3. Print recent messages to console")
        print("4. Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            limit_input = input("Number of messages to export (or 'all'): ").strip()
            limit = None if limit_input.lower() == "all" else int(limit_input or "100")

            filename = f"{title.replace(' ', '_').lower()}_messages.json"
            output_path = Path(__file__).parent / filename

            logger.info(f"Exporting to {output_path}...")
            await client.export_to_json(group, output_path, limit)
            print(f"\nMessages exported to: {output_path}")

        elif choice == "2":
            logger.info("Listening for new messages. Press Ctrl+C to stop.")

            async def print_message(msg):
                time_str = msg.date.split("T")[1].split(".")[0] if "T" in msg.date else msg.date
                print(f"[{time_str}] {msg.sender_name}: {msg.text[:100]}")
                if msg.media_type:
                    print(f"         [Media: {msg.media_type}]")

            try:
                await client.listen_for_updates(group, print_message)
            except KeyboardInterrupt:
                logger.info("Stopped listening")

        elif choice == "3":
            count = int(input("How many recent messages? ").strip() or "10")
            messages = await client.get_messages(group, limit=count)

            print(f"\n--- Recent {len(messages)} messages ---\n")

            # Print in chronological order (oldest first)
            for msg in reversed(messages):
                date_str = msg.date.split("T")[0] if "T" in msg.date else msg.date
                time_str = msg.date.split("T")[1].split(".")[0] if "T" in msg.date else ""

                print(f"[{date_str} {time_str}] {msg.sender_name}")
                if msg.text:
                    # Indent message text
                    for line in msg.text.split("\n"):
                        print(f"  {line}")
                if msg.media_type:
                    print(f"  [Media: {msg.media_type}]")
                if msg.forward_from:
                    print(f"  [Forwarded from: {msg.forward_from}]")
                print()

        elif choice == "4" or not choice:
            logger.info("Goodbye!")

        else:
            logger.error("Invalid choice")

    finally:
        await client.disconnect()

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
