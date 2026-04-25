#!/usr/bin/env python3

import asyncio

from app.utils.seed import seed


if __name__ == "__main__":
    asyncio.run(seed())
