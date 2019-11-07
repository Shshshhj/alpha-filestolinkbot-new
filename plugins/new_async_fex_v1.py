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
        text='📤 Uploading file...',
        chat_id=update.chat.id,
        message_id=a.message_id
    )
    
    filesize = os.path.getsize(after_download_file_name)
    filename = os.path.basename(after_download_file_name)

    # upload
    session = aiohttp.ClientSession()
    async with session.get('https://api.fex.net/api/v1/anonymous/upload-token') as resp:
        token = json.loads((await resp.text()))['token']
        
    print(token)
    
    data = {'directory_id':None, 'size':filesize, 'name':filename}
    headers = {
        'Authorization': 'Bearer ' + token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0',
        'Accept': '*/*',
        'Accept-Language': ' en-US,en;q=0.5',
        'Accept-Encoding': ' gzip, deflate, br',
        'Referer': ' https://fex.net/a',
        'Content-Type': ' application/json',
        'Origin': ' https://fex.net',
        'Connection': ' keep-alive',
        'Pragma': ' no-cache',
        'Cache-Control': ' no-cache',
        'TE': ' Trailers'
    }
    async with session.post('https://api.fex.net/api/v1/anonymous/file', data=json.dumps(data), headers=headers) as resp:
        file_upload = json.loads(await resp.text())
        print(file_upload['location'])
        
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://fex.net/a',
        'Content-Type': 'application/json',
        'Fsp-Size': str(filesize),
        'Fsp-Version': '1.0.0',
        'Fsp-FileName': filename,
        'Origin': 'https://fex.net',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
        'TE': 'Trailers',
        }
            
    async with session.post(file_upload['location'], headers=headers) as resp:
        pass
    
    url = file_upload['location']
    max_days = "7"
    command_to_exec = [
            "curl",
            # "-g",
            # '-v',
            # '--progress-bar',
            '-X', 'PATCH',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0',
            '-H', 'Referer: https://fex.net/a',
            '-H', 'Authorization: Bearer ' + token,
            '-H', 'Content-Type: application/offset+octet-stream',
            '-H', 'Fsp-Version: 1.0.0',
            '-H', 'Fsp-Offset: 0',
            '-H', 'Fsp-FileName: ' + filename,
            '-H', 'Origin: https://fex.net',
            '-H', 'Content-Length: ' + str(filesize),
            '-H', 'Connection: keep-alive',
            '-H', 'Pragma: no-cache',
            '-H', 'Cache-Control: no-cache',
            '-H', 'TE: Trailers',
            '-T', "test.txt",
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
        
        download = json.loads(response)
        await bot.edit_message_text(
            chat_id=update.chat.id,
            text=Translation.AFTER_GET_DL_LINK.format(
                filename,
                await humanbytes(filesize),
                max_days,
                download['download_url']
            ),
            parse_mode="html",
            message_id=a.message_id,
            disable_web_page_preview=True
        )
        await session.close()
        return       
    
    try:
        users.remove(update.from_user.id)
        os.remove(after_download_file_name)
    except:
        pass
