# ----------------------------------- https://github.com/m4mallu/clonebot ---------------------------------------------#
# Monkey-patch Pyrogram 2.0.106 to support newer Telegram channel IDs beyond the old 32-bit limit.
# Telegram now assigns channel IDs that exceed the original MIN_CHANNEL_ID (-1002147483647).
# This patch extends the range to support IDs up to -1009999999999.

import pyrogram.utils as utils

# Extend the minimum channel ID to support newer large channel IDs
utils.MIN_CHANNEL_ID = -1009999999999
