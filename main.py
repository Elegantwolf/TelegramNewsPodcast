import json
import os
import datetime
import pytz
import asyncio

from getdata import getdata

# --- 配置项 ---
# Telegram API credentials are loaded from the environment at runtime.
API_ID_ENV_VAR = 'TELEGRAM_API_ID'
API_HASH_ENV_VAR = 'TELEGRAM_API_HASH'

# The default session path is local client state, never the NAS archive.
DEFAULT_SESSION_PATH = os.path.expanduser(
    '~/.config/telegram-news-podcast/telegram.session'
)
SESSION_NAME = os.environ.get('TELEGRAM_SESSION_PATH', DEFAULT_SESSION_PATH)

# 3. 目标频道信息
# 可以是频道的用户名 (如 '@channelusername') 或 频道的ID (如 -1001234567890)
# 如果是ID，确保它是整数类型。如果是用户名，则是字符串。
CHANNEL_IDENTIFIER = '@DNSPODT'  # 例如: '@TelegramTips' 或 -1001234567890

# 4. 定义当天要获取消息的时间范围 (使用24小时制)
# 例如: 从早上 9:00 到下午 5:00
INTERVAL_HOURS = "24:00"  # 持续时间 (HH:MM)
END_TIME_STR = "17:00"    # 结束时间 (HH:MM)

# 5. JSON 文件输出目录 (可选, 留空则保存在脚本同级目录)
OUTPUT_DIR = "telegram_archives"
# --- 配置结束 ---


def _required_environment_value(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "See .env.example and README.md."
        )
    return value


def load_telegram_credentials():
    """Load Telegram API credentials without printing their values."""

    api_id_raw = _required_environment_value(API_ID_ENV_VAR)
    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        raise RuntimeError(f"{API_ID_ENV_VAR} must be an integer.") from exc

    api_hash = _required_environment_value(API_HASH_ENV_VAR)
    return api_id, api_hash


async def main():
    api_id, api_hash = load_telegram_credentials()

    await getdata(
        API_ID=api_id,
        API_HASH=api_hash,
        SESSION_NAME=SESSION_NAME,
        CHANNEL_IDENTIFIER=CHANNEL_IDENTIFIER,
        INTERVAL_HOURS_STR=INTERVAL_HOURS,
        END_TIME_STR=END_TIME_STR,
        OUTPUT_DIR=OUTPUT_DIR
    )


if __name__ == "__main__":
    # 创建输出目录
    if OUTPUT_DIR and not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 运行主函数
    asyncio.run(main())
