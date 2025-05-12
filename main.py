import json
import os
import datetime
import pytz
import asyncio

from getdata import getdata

# --- 配置项 ---
# 1. 替换为你的 API ID 和 API Hash
API_ID = 28274300  # 替换成你的 API ID (整数)
API_HASH = 'e3cdc41cd8786b45efd2ae4dcb9662bb'  # 替换成你的 API Hash (字符串)

# 2. 会话文件名 (用于保存登录信息)
SESSION_NAME = 'my_telegram_session'

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

async def main():

    await getdata(
        API_ID=API_ID,
        API_HASH=API_HASH,
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