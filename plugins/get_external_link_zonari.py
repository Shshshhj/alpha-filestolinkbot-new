#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
#import requests
import subprocess
import time
import asyncio

# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)

from helper_funcs.display_progress import progress_for_pyrogram


@pyrogram.Client.on_message()
async def get_link(bot, update):
    # print(update)
    if update.text == "/start":
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.START_TEXT,
            reply_to_message_id=update.message_id
        )
        return False
    elif update.text == "/help" or update.text == "/about":
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.HELP_USER,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_to_message_id=update.message_id
        )
        return False
    elif update.reply_to_message is not None and update.text == "/getlink":
        reply_message = update.reply_to_message
    elif update.reply_to_message is None and update.text == "/getlink":
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.REPLY_TO_DOC_GET_LINK,
            reply_to_message_id=update.message_id
        )
        return False
    elif update.document is not None or update.video is not None or update.photo is not None or update.audio is not None or update.animation is not None or update.voice is not None or update.sticker is not None or update.video_note is not None:
        reply_message = update
    else:
        return False

    # print(update)
    if str(update.from_user.id) in Config.BANNED_USERS:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.ABUSIVE_USERS,
            reply_to_message_id=update.message_id,
            disable_web_page_preview=True,
            parse_mode="html"
        )
        return
    logger.info(update.from_user)

    download_location = Config.DOWNLOAD_LOCATION + "/"
    a = await bot.send_message(
        chat_id=update.chat.id,
        text=Translation.DOWNLOAD_START,
        reply_to_message_id=update.message_id
    )
    c_time = time.time()
    after_download_file_name = await bot.download_media(
        message=reply_message,
        file_name=download_location,
        progress=progress_for_pyrogram,
        progress_args=(
            bot,
            Translation.DOWNLOAD_START,
            a.message_id,
            update.chat.id,
            c_time
        )
    )
    #download_extension = after_download_file_name.rsplit(".", 1)[-1]
    await bot.edit_message_text(
        text=Translation.SAVED_RECVD_DOC_FILE,
        chat_id=update.chat.id,
        message_id=a.message_id
    )

    #filesize = os.path.getsize(after_download_file_name)
    filename = os.path.basename(after_download_file_name)
    
    url = "https://transfer.zonari.us/{}".format(filename)
    max_days = "2"
    command_to_exec = [
        "curl", "-g",
        # "-H", 'Max-Downloads: 999',
        "-H", 'Max-Days: 2', # + max_days + '',
        "--upload-file", after_download_file_name,
        url
    ]

    await bot.edit_message_text(
        text=Translation.UPLOAD_START,
        chat_id=update.chat.id,
        message_id=a.message_id
    )
    logger.info(command_to_exec)
    t_response = await asyncio.create_subprocess_exec(
        *command_to_exec,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    if t_response.returncode:
        logger.info(f"Status : FAIL {t_response.stderr}")
        await bot.edit_message_text(
            chat_id=update.chat.id,
            text=exc.output.decode("UTF-8"),
            message_id=a.message_id
        )
        return False
    else:
        logger.info(t_response.stdout)
        link = t_response.stdout.decode()

        #shorten_api_url = "http://ouo.io/api/{}?s={}".format(Config.OUO_IO_API_KEY, t_response_arry)
        #adfulurl = requests.get(shorten_api_url).text
        
    await bot.edit_message_text(
        chat_id=update.chat.id,
        text=Translation.AFTER_GET_DL_LINK.format(link, max_days),
        parse_mode="html",
        message_id=a.message_id,
        disable_web_page_preview=True
    )
    try:
        os.remove(after_download_file_name)
    except:
        pass
