# ----------------------------------- https://github.com/m4mallu/clonebot ---------------------------------------------#
import time
import pytz
import asyncio
from bot import Bot
from math import trunc
from library.sql import *
from presets import Presets
from datetime import datetime
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from library.buttons import reply_markup_stop, reply_markup_finished
from library.chat_support import calc_percentage, calc_progress, save_target_cfg, set_to_defaults, date_time_calc
#
bot_start_time = time.time()
#
async def clone_medias(bot: Bot, m: Message):
    id = int(m.chat.id)
    query = await query_msg(id)
    clone_cancel_key[id] = int(m.id)
    #
    start_time = time.time()
    start_date = datetime.today().strftime("%d/%m/%y")
    clone_start_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
    #
    file_name = caption = report = str()
    processed_media_groups = set()
    #
    delay = limit = doc = video = audio = text = voice = photo = total_copied = matching = msg_id = int()
    #
    # Create mandatory variables from the database query
    source_chat = int(query.s_chat)
    target_chat = int(query.d_chat)
    start_id = int(query.from_id)
    end_id = int(query.to_id)
    end_msg_id = int(query.last_msg_id)
    #
    clone_delay = bool(query.delayed_clone)
    default_caption = bool(query.caption)
    fn_caption = bool(query.file_caption)
    #
    # Define the clone delay
    if bool(clone_delay):
        delay = 10
    else:
        delay = 3
    #
    # The values will be switched if the start message id is greater than the end message id
    if start_id > end_id:
        start_id = start_id ^ end_id
        end_id = end_id ^ start_id
        start_id = start_id ^ end_id
    else:
        pass
    #
    # Creating variables for progress bar and the percentage calculation
    if not bool(start_id):
        sp = 0
    else:
        sp = start_id
    if not bool(end_id):
        ep = end_msg_id
    else:
        ep = end_id
    #
    await m.edit_text(Presets.INITIAL_MESSAGE_TEXT)
    await asyncio.sleep(1)
    msg = await m.reply_text(Presets.WAIT_MSG, reply_markup=reply_markup_stop)
    #
    for offset in reversed(
            range(end_id+1, (1 if not bool(start_id) else start_id)-1, (start_id - 1) if not bool(start_id) else -1)):
        async for user_message in bot.USER.get_chat_history(chat_id=source_chat, offset_id=offset, limit=1):
            if not user_message.empty:
                messages = await bot.USER.get_messages(source_chat, user_message.id, replies=0)
                msg_id = messages.id
                cur_time = time.time()
                cur_date = datetime.today().strftime("%d/%m/%y")
                days, hours = await date_time_calc(start_date, start_time, cur_date, cur_time)
                #
                report = Presets.CLONE_REPORT.format(time.strftime("%I:%M %p"), source_chat, target_chat,
                                                     "1" if not bool(start_id) else start_id,
                                                     end_msg_id if not bool(msg_id) else msg_id,
                                                     "🟡" if bool(clone_delay) else "🚫",
                                                     "🟡" if bool(default_caption) else "🚫",
                                                     "🟡" if bool(fn_caption) else "🚫",
                                                     int(total_copied), doc, video, audio, photo, voice, text, matching)
                # If the user cancelled the clone operation
                if id not in clone_cancel_key:
                    await save_target_cfg(id, target_chat)
                    if not int(total_copied):
                        await m.delete()
                    await asyncio.sleep(2)
                    await msg.edit(Presets.CANCELLED_MSG, reply_markup=reply_markup_finished)
                    await bot.USER.send_message("me", report, disable_web_page_preview=True)
                    await set_to_defaults(id)
                    return
                else:
                    pass
                media_group_id = getattr(messages, "media_group_id", None)
                if media_group_id in processed_media_groups:
                    continue
                allow_group_copy = (
                    bool(media_group_id)
                    and bool(default_caption)
                    and (id not in custom_caption)
                    and not bool(fn_caption)
                )
                if allow_group_copy and media_group_id not in processed_media_groups and hasattr(bot.USER, "copy_media_group"):
                    processed_media_groups.add(media_group_id)
                    group_messages = None
                    if hasattr(bot.USER, "get_media_group"):
                        try:
                            group_messages = await bot.USER.get_media_group(source_chat, messages.id)
                        except Exception:
                            group_messages = None
                    if not group_messages:
                        group_messages = [messages]
                    for gm in group_messages:
                        for file_type in file_types:
                            if file_type == "text":
                                continue
                            media = getattr(gm, file_type, None)
                            if media is None:
                                continue
                            uid = str(media.file_unique_id) if hasattr(media, 'file_unique_id') else None
                            if (uid is not None) and (uid in master_index):
                                matching += 1
                            else:
                                if uid is not None:
                                    master_index.append(uid)
                                if file_type == 'document': doc += 1
                                elif file_type == 'video': video += 1
                                elif file_type == 'audio': audio += 1
                                elif file_type == "voice": voice += 1
                                elif file_type == "photo": photo += 1
                                elif file_type == "text": text += 1
                                else: pass
                    total_copied = doc + video + audio + voice + photo + text
                    pct = await calc_percentage(sp, ep, msg_id)
                    update_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
                    try:
                        await m.edit(
                            Presets.MESSAGE_COUNT.format(
                                int(msg_id),
                                int(total_copied),
                                trunc(pct) if pct <= 100 else "- ",
                                days,
                                hours,
                                clone_start_time,
                                update_time
                            ),
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except Exception:
                        pass
                    progress = await calc_progress(pct)
                    try:
                        # Build InputMedia list manually to preserve premium emoji entities in captions
                        input_media_list = []
                        for gm in group_messages:
                            file_id = None
                            media_type = None
                            if gm.photo:
                                file_id = gm.photo.file_id
                                media_type = "photo"
                            elif gm.video:
                                file_id = gm.video.file_id
                                media_type = "video"
                            elif gm.document:
                                file_id = gm.document.file_id
                                media_type = "document"
                            elif gm.audio:
                                file_id = gm.audio.file_id
                                media_type = "audio"
                            if file_id is None:
                                continue
                            # Preserve original caption and entities (including premium/custom emojis)
                            gm_caption = gm.caption or ""
                            gm_caption_entities = gm.caption_entities
                            if media_type == "photo":
                                input_media_list.append(InputMediaPhoto(
                                    media=file_id,
                                    caption=gm_caption,
                                    caption_entities=gm_caption_entities,
                                    parse_mode=None
                                ))
                            elif media_type == "video":
                                input_media_list.append(InputMediaVideo(
                                    media=file_id,
                                    caption=gm_caption,
                                    caption_entities=gm_caption_entities,
                                    parse_mode=None
                                ))
                            elif media_type == "document":
                                input_media_list.append(InputMediaDocument(
                                    media=file_id,
                                    caption=gm_caption,
                                    caption_entities=gm_caption_entities,
                                    parse_mode=None
                                ))
                            elif media_type == "audio":
                                input_media_list.append(InputMediaAudio(
                                    media=file_id,
                                    caption=gm_caption,
                                    caption_entities=gm_caption_entities,
                                    parse_mode=None
                                ))
                        if input_media_list:
                            await bot.USER.send_media_group(
                                chat_id=target_chat,
                                media=input_media_list
                            )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except Exception:
                        await msg.edit_text(Presets.COPY_ERROR, reply_markup=reply_markup_finished)
                        await bot.USER.send_message("me", report, disable_web_page_preview=True)
                        await set_to_defaults(id)
                        if not int(total_copied):
                            await m.delete()
                        return
                    try:
                        await msg.edit("🇮🇳 | " + progress if pct <= 100 else Presets.BLOCK,
                                       reply_markup=reply_markup_stop)
                    except Exception:
                        pass
                    await asyncio.sleep(delay)
                    if end_id and (int(msg_id) >= end_id):
                        if not int(total_copied):
                            await m.delete()
                        await msg.edit(Presets.FINISHED_TEXT, reply_markup=reply_markup_finished)
                        await bot.USER.send_message("me", report, disable_web_page_preview=True)
                        await set_to_defaults(id)
                        return
                    else:
                        pass
                    continue
                for file_type in file_types:
                    media = getattr(messages, file_type, None)
                    if media is not None:
                        uid = str(media.file_unique_id) if hasattr(media, 'file_unique_id') else None
                        # If the duplicate file id is found while cloning operation
                        if (uid is not None) and (uid in master_index):
                            matching += 1
                            await m.edit(Presets.DUPLICATE_INDEX.format(matching, msg_id))
                        # if the duplicate file is not found while cloning
                        else:
                            if uid is not None:
                                master_index.append(uid) # The unique id of the file is added to the master index list
                            if file_type == 'document': doc += 1; file_name = messages.document.file_name
                            elif file_type == 'video': video += 1; file_name = messages.video.file_name
                            elif file_type == 'audio': audio += 1; file_name = messages.audio.file_name
                            elif file_type == "voice": voice += 1; file_name = messages.caption
                            elif file_type == "photo": photo += 1; file_name = messages.caption
                            elif file_type == "text": text += 1; file_name = str()
                            else: pass
                            #
                            caption = None
                            caption_entities = None
                            override_caption = False
                            if (file_type != "text") and (id in custom_caption):
                                custom_value = custom_caption.get(id)
                                if isinstance(custom_value, dict):
                                    caption = custom_value.get("text", "")
                                    caption_entities = custom_value.get("entities")
                                else:
                                    caption = custom_value
                                override_caption = True
                            elif bool(fn_caption):
                                try:
                                    caption = str(file_name).rsplit('.', 1)[0] if file_name else ""
                                except Exception:
                                    caption = ""
                                override_caption = True
                            elif (file_type != "text") and (not bool(default_caption)):
                                # Explicitly strip captions when captions are disabled
                                caption = ""
                                caption_entities = None
                                override_caption = True
                            #
                            total_copied = doc + video + audio + voice + photo + text
                            pct = await calc_percentage(sp, ep, msg_id)
                            update_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
                            try:
                                await m.edit(
                                    Presets.MESSAGE_COUNT.format(
                                        int(msg_id),
                                        int(total_copied),
                                        trunc(pct) if pct <= 100 else "- ",
                                        days,
                                        hours,
                                        clone_start_time,
                                        update_time
                                    ),
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True
                                )
                            except FloodWait as e:
                                await asyncio.sleep(e.value)
                            except Exception:
                                pass
                            progress = await calc_progress(pct)
                            try:
                                copy_kwargs = dict(
                                    chat_id=target_chat,
                                    from_chat_id=source_chat,
                                    message_id=msg_id,
                                    reply_markup=messages.reply_markup,
                                    disable_notification=True
                                )
                                if override_caption:
                                    copy_kwargs["caption"] = caption if caption is not None else ""
                                    if caption_entities:
                                        copy_kwargs["caption_entities"] = caption_entities
                                        copy_kwargs["parse_mode"] = None
                                await bot.USER.copy_message(**copy_kwargs)
                            except FloodWait as e:
                                await asyncio.sleep(e.value)
                            except Exception:
                                await msg.edit_text(Presets.COPY_ERROR, reply_markup=reply_markup_finished)
                                await bot.USER.send_message("me", report, disable_web_page_preview=True)
                                await set_to_defaults(id)
                                if not int(total_copied):
                                    await m.delete()
                                return
                            try:
                                await msg.edit("🇮🇳 | " + progress if pct <= 100 else Presets.BLOCK,
                                               reply_markup=reply_markup_stop)
                            except Exception:
                                pass
                            await asyncio.sleep(delay)
                            # If the end id is reached, the clone operation will be aborted and the report is generated
                            if end_id and (int(msg_id) >= end_id):
                                if not int(total_copied):
                                    await m.delete()
                                await msg.edit(Presets.FINISHED_TEXT, reply_markup=reply_markup_finished)
                                await bot.USER.send_message("me", report, disable_web_page_preview=True)
                                await set_to_defaults(id)
                                return
                            else:
                                pass
                    else:
                        pass
            else:
                pass

    # If the clone operation is automatically completed by the bot
    await save_target_cfg(id, target_chat)
    if not int(total_copied):
        await m.delete()
    await m.edit_reply_markup(None)
    await msg.edit(Presets.FINISHED_TEXT, reply_markup=reply_markup_finished)
    await bot.USER.send_message("me", report, disable_web_page_preview=True)
    await set_to_defaults(id)
