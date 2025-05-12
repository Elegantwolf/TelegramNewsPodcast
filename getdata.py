import json
import asyncio
from datetime import datetime, time, timedelta
import pytz # For timezone handling
from datetime import datetime, time, timedelta

from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel # For channel access by ID


async def getdata(API_ID, API_HASH, SESSION_NAME, CHANNEL_IDENTIFIER, INTERVAL_HOURS_STR, END_TIME_STR, OUTPUT_DIR,local_tz=pytz.timezone('Asia/Tokyo')):
    # # 获取本地时区
    # local_tz = pytz.timezone('Asia/Tokyo')  # 替换为你的时区，例如 'Asia/Tokyo'
    # 解析时间字符串
    try:
        interval_hour, interval_minute = map(int, INTERVAL_HOURS_STR.split(':'))
        end_hour, end_minute = map(int, END_TIME_STR.split(':'))
        end_datetime_local = local_tz.localize(datetime.combine(datetime.today(), time(end_hour, end_minute)))
        interval = timedelta(hours=interval_hour, minutes=interval_minute)
        start_datetime_local = end_datetime_local - interval
        print(f"开始时间: {start_datetime_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"结束时间: {end_datetime_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except ValueError:
        print("错误：开始时间或结束时间格式不正确。请使用 HH:MM 格式。")
        return


    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        print("正在连接到 Telegram...")
        if not client.is_connected():
            await client.connect()

        if not client.is_user_authorized():
            print("需要登录。请输入手机号和验证码。")
            await client.send_code_request(await client.get_me(input_phone=True)) # 获取手机号
            await client.sign_in(code=input("请输入收到的验证码: "))
            if client.is_user_authorized() and client.two_step_verification_needed():
                client.sign_in(password=input("请输入两步验证密码: "))
        
        me = await client.get_me()
        print(f"已作为 {me.first_name} (@{me.username}) 登录。")

        try:
            print(f"正在获取频道信息: {CHANNEL_IDENTIFIER}...")
            channel_entity = await client.get_entity(CHANNEL_IDENTIFIER)
            print(f"成功获取频道: {getattr(channel_entity, 'title', str(CHANNEL_IDENTIFIER))}")
        except ValueError:
            print(f"错误: 无法找到频道 '{CHANNEL_IDENTIFIER}'. 请检查是否正确 (用户名需要带 '@', ID 为负数长整数)。")
            return
        except Exception as e:
            print(f"获取频道时发生错误: {e}")
            return

        fetched_messages = []
        print(f"开始从频道获取消息 (从 {end_datetime_local.strftime('%Y-%m-%d %H:%M:%S %Z')} 开始向前回溯)...")


        start_datetime_utc = start_datetime_local.astimezone(pytz.utc)
        end_datetime_utc = end_datetime_local.astimezone(pytz.utc)

        message_count = 0
        async for message in client.iter_messages(
            channel_entity,
            limit=None,
            reverse=False,  # 新到旧
            offset_date=end_datetime_utc  # 只获取比end_datetime_utc更早的消息
        ):
            if message.date < start_datetime_utc:
                break  # 已经早于窗口，停止

            if message.text:
                msg_local_dt = message.date.astimezone(local_tz)
                if start_datetime_local <= msg_local_dt <= end_datetime_local:
                    sender_id_str = str(message.sender_id) if message.sender_id else None
                    fetched_messages.append({
                        'id': message.id,
                        'date_utc': message.date.isoformat(),
                        'date_local': msg_local_dt.isoformat(),
                        'sender_id': sender_id_str,
                        'text': message.text
                    })
                    message_count += 1
                    if message_count % 50 == 0:
                        print(f"  已处理 {message_count} 条在时间窗口内的潜在消息...")

        print(f"获取完成。共找到 {len(fetched_messages)} 条符合条件的文字消息。")

        if fetched_messages:
            # 创建输出目录 (如果不存在)
            import os
            if OUTPUT_DIR and not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            channel_name_sanitized = "".join(c if c.isalnum() else "_" for c in str(getattr(channel_entity, 'username', CHANNEL_IDENTIFIER)))
            if not channel_name_sanitized or channel_name_sanitized.startswith("_"):
                channel_name_sanitized = f"channel_{channel_entity.id}"


            filename_ts = f"{end_datetime_local.strftime('%Y-%m-%d')}"
            output_filename = f"{channel_name_sanitized}_messages_{filename_ts}.json"
            
            if OUTPUT_DIR:
                output_filepath = os.path.join(OUTPUT_DIR, output_filename)
            else:
                output_filepath = output_filename

            print(f"正在将消息保存到: {output_filepath}")
            try:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump(fetched_messages, f, ensure_ascii=False, indent=4)
                print("消息已成功保存为 JSON 文件。")
            except IOError as e:
                print(f"错误: 无法写入 JSON 文件: {e}")
        else:
            print("在指定的时间范围内没有找到符合条件的文字消息。")

if __name__ == '__main__':
    # 在Windows上，asyncio可能会因为默认的事件循环策略出问题
    # if os.name == 'nt':
    #    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(getdata())