#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import aiohttp
import uuid
import re

import os
import subprocess
import time
import asyncio
from tools.config import Config
from tools.progress import progress_for_pyrogram, humanbytes
from tools.translation import Translation
import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
users = []


@pyrogram.Client.on_message()
async def get_link(bot, update):
    if str(update.from_user.id) in Config.BANNED_USERS:
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
    if update.from_user.id not in users:
        users.append(update.from_user.id)
    #else:
        #await bot.send_message(
            #chat_id=update.chat.id,
            #text=Translation.ABS_TEXT,
            #reply_to_message_id=update.message_id
        #)
        #return
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
            Translation.DOWNLOADING,
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

    # upload
    session = aiohttp.ClientSession()
    async with session.get('https://files.fm/') as resp:
        m = re.search('PHPSESSID=(.+?);', str(resp.cookies))
        if m:
            phpsessionid = m.group(1)
        else:
            await bot.edit_message_text(
                text='Failed to fetch required data!',
                chat_id=update.chat.id,
                message_id=a.message_id
            )
            await session.close()
            return
    
    async with session.get('https://files.fm/server_scripts/get_upload_id.php?show_add_key=1', cookies={'PHPSESSID':phpsessionid}) as resp:
        upload_id = (await resp.text()).split(',') # ['avwhp4sx', 'fbe1de92', '465d7']
    
    uuidstr = str(uuid.uuid4())
    
    url = 'https://free.files.fm/save_file.php?PHPSESSID={}&up_id={}&ignore_user_abort=1&skip_update=1&key={}&v={}'.format(phpsessionid, upload_id[0], upload_id[2], str(int(time.time())))
    max_days = "7"
    command_to_exec = [
        "curl",
        "-g",
        '-H', "Transfer-Encoding: chunked",
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0',
        '-H', 'X-File-Upload: uploadingfiles',
        '-F', 'APC_UPLOAD_PROGRESS=' + uuidstr,
        '-F', 'PHP_SESSION_UPLOAD_PROGRESS=' + uuidstr,
        '-F', 'UPLOAD_IDENTIFIER=' + uuidstr,
        '-F', "Filedata=@" + after_download_file_name,
        url
    ]

    await bot.edit_message_text(
        text=Translation.UPLOAD_START,
        chat_id=update.chat.id,
        message_id=a.message_id
    )
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode:
        error = f"ERROR: {stderr.decode()}"
        logger.info(error)
        await bot.edit_message_text(
            chat_id=update.chat.id,
            text=error,
            message_id=a.message_id
        )
        users.remove(update.from_user.id)
        await session.close()
        return
    else:
        response = stdout.decode()
        logger.info(response)
        
        if response.strip() == 'd':
            async with session.get('https://free.files.fm/finish_upload.php', params={'upload_hash':upload_id[0]}) as resp:
                if (await resp.text()) == 'var ok=1':
                    link = 'https://files.fm/u/' + upload_id[0]
                    
                    async with session.get(link) as resp:
                        # print(await resp.text())
                        m = re.search('tools_button_download"\s+href="(https?://.+?)"', (await resp.text()))
                        if m:
                            print(m.group(1))
                            await bot.edit_message_text(
                                chat_id=update.chat.id,
                                text=Translation.AFTER_GET_DL_LINK.format(
                                    filename,
                                    await humanbytes(filesize),
                                    max_days,
                                    m.group(1)
                                ),
                                parse_mode="html",
                                message_id=a.message_id,
                                disable_web_page_preview=True
                            )
                            await session.close()
                            return
                            
                        else:
                            await bot.edit_message_text(
                                chat_id=update.chat.id,
                                text=Translation.AFTER_GET_DL_LINK.format(
                                    filename,
                                    await humanbytes(filesize),
                                    max_days,
                                    link
                                ),
                                parse_mode="html",
                                message_id=a.message_id,
                                disable_web_page_preview=True
                            )
                            await session.close()
                            return
                else:
                    await bot.edit_message_text(
                        text='Failed to fetch required data!',
                        chat_id=update.chat.id,
                        message_id=a.message_id
                    )
                    await session.close()
                    return
                    
    
    try:
        users.remove(update.from_user.id)
        os.remove(after_download_file_name)
    except:
        pass
