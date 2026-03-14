import asyncio
import os
import sys
# This is a bit of a hack to allow the script to be run from the root of the project
# and find the 'app' module. A better solution would be to make this a proper CLI command
# with the project installed in editable mode.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.seeder import seed_data


if __name__ == "__main__":
    print("Running manual data seeding...")
    asyncio.run(seed_data())
    print("Manual data seeding finished.")
