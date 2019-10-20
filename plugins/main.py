#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
import subprocess
import time
import asyncio
from tools.config import Config
from tools.progress import progress_for_pyrogram
from tools.translation import Translation
import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
users = []


@pyrogram.Client.on_message()
async def get_link(bot, update):
    if update.from_user.id in Config.BANNED_USERS:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.ABUSIVE_USERS,
            reply_to_message_id=update.message_id,
            disable_web_page_preview=True,
            parse_mode="html"
        )
        return
    elif update.text == "/start":
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.START_TEXT,
            reply_to_message_id=update.message_id
        )
        return
    elif update.text == "/help" or update.text == "/about":
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.HELP_USER,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_to_message_id=update.message_id
        )
        return
    elif update.document is not None or update.video is not None or update.photo is not None or update.audio is not None or update.animation is not None or update.voice is not None or update.sticker is not None or update.video_note is not None:
        reply_message = update
    else:
        return
    logger.info(update.from_user)
    if update.from_user.id not in users:
        users.append(update.from_user.id)
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.ABS_TEXT,
            reply_to_message_id=update.message_id
        )
        return
    download_location = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + "/"
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
    await bot.edit_message_text(
        text=Translation.SAVED_RECVD_DOC_FILE,
        chat_id=update.chat.id,
        message_id=a.message_id
    )
    filesize = os.path.getsize(after_download_file_name)
    filename = os.path.basename(after_download_file_name)

    url = "https://transfer.zonari.us/{}".format(filename)
    max_days = "2"
    command_to_exec = [
        "curl",
        "-g",
        # "-H",
        # 'Max-Downloads: 999',
        "-H",
        'Max-Days: 2', # + max_days + '',
        "--upload-file",
        after_download_file_name,
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
        error = f"ERROR: {t_response.stderr}"
        logger.info(error)
        await bot.edit_message_text(
            chat_id=update.chat.id,
            text=error,
            message_id=a.message_id
        )
        users.remove(update.from_user.id)
        return
    else:
        logger.info(t_response.stdout)
        link = t_response.stdout
    await bot.edit_message_text(
        chat_id=update.chat.id,
        text=Translation.AFTER_GET_DL_LINK.format(
            link,
            filename,
            filesize,
            max_days
        ),
        parse_mode="html",
        message_id=a.message_id,
        disable_web_page_preview=True
    )
    try:
        users.remove(update.from_user.id)
        os.remove(after_download_file_name)
    except:
        pass