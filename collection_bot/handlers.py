"""Telegram conversation: consent, demographics, then two photos per emotion."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from collection_bot.config import owner_id
from collection_bot.faces import inspect
from collection_bot.schema import (
    AGE_BANDS,
    EMOTIONS,
    GENDERS,
    LANGUAGES,
    REGIONS,
    TOTAL_PHOTOS,
)
from collection_bot.storage import DatasetStore, next_request, stage
from collection_bot.texts import emotion_label, photo_prompt, region_label, t

LANG, AGE_GATE, CONSENT, AGE_BAND, REGION, GENDER, PHOTO, EXAMPLE = range(8)

MAX_DOCUMENT_BYTES = 8_000_000
logger = logging.getLogger(__name__)


def _store(context: ContextTypes.DEFAULT_TYPE) -> DatasetStore:
    return context.application.bot_data["store"]


def _lang(context: ContextTypes.DEFAULT_TYPE, meta: dict | None = None) -> str:
    if meta and meta.get("language") in LANGUAGES:
        return meta["language"]
    chosen = context.user_data.get("lang")
    if chosen in LANGUAGES:
        return chosen
    return "uz"


def _rows(buttons: list[tuple[str, str]], columns: int = 1) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    current: list[InlineKeyboardButton] = []
    for label, data in buttons:
        current.append(InlineKeyboardButton(label, callback_data=data))
        if len(current) == columns:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    return InlineKeyboardMarkup(rows)


def _is_forward(message) -> bool:
    return bool(
        getattr(message, "forward_origin", None)
        or getattr(message, "forward_from", None)
        or getattr(message, "forward_date", None)
    )


def _image_file(message):
    if message.photo:
        return message.photo[-1]
    document = message.document
    if document and (document.mime_type or "").startswith("image/"):
        return document
    return None


async def _show_stage(
    message,
    context: ContextTypes.DEFAULT_TYPE,
    meta: dict,
    *,
    prefix: str = "",
) -> int:
    lang = _lang(context, meta)
    current = stage(meta)
    saved = len(meta.get("photos", []))
    if current == "age_band":
        buttons = [(band, f"age:{band}") for band in AGE_BANDS if band != "prefer_not"]
        buttons.append((t(lang, "prefer_not"), "age:prefer_not"))
        text = t(lang, "ask_age_band")
        markup = _rows(buttons, columns=2)
        state = AGE_BAND
    elif current == "region":
        buttons = [(region_label(lang, code), f"reg:{code}") for code in REGIONS]
        text = t(lang, "ask_region")
        markup = _rows(buttons)
        state = REGION
    elif current == "gender":
        buttons = [
            (t(lang, "female"), "gen:female"),
            (t(lang, "male"), "gen:male"),
            (t(lang, "prefer_not"), "gen:prefer_not"),
        ]
        text = t(lang, "ask_gender")
        markup = _rows(buttons)
        state = GENDER
    elif current == "photo":
        emotion, shot = next_request(meta)
        text = photo_prompt(lang, emotion, shot, saved, TOTAL_PHOTOS)
        markup = None
        state = PHOTO
    elif current == "example":
        buttons = [
            (t(lang, "example_yes"), "ex:yes"),
            (t(lang, "example_no"), "ex:no"),
        ]
        text = t(lang, "ask_example")
        markup = _rows(buttons)
        state = EXAMPLE
    else:
        text = t(
            lang,
            "thanks",
            count=saved,
            participant_id=meta["participant_id"],
        )
        markup = None
        state = ConversationHandler.END
    if prefix:
        text = f"{prefix}\n\n{text}"
    await message.reply_text(text, reply_markup=markup)
    return state


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.effective_message
    if update.effective_chat is None or update.effective_chat.type != "private":
        await message.reply_text(t("uz", "private_only"))
        return ConversationHandler.END
    meta = _store(context).get(update.effective_user.id)
    if meta is None:
        context.user_data.clear()
        await message.reply_text(
            t("uz", "choose_language"),
            reply_markup=_rows(
                [("O‘zbekcha", "lang:uz"), ("Русский", "lang:ru"), ("English", "lang:en")],
            ),
        )
        return LANG
    context.user_data["lang"] = meta["language"]
    if stage(meta) == "complete":
        await message.reply_text(
            t(
                meta["language"],
                "already_done",
                participant_id=meta["participant_id"],
            )
        )
        return ConversationHandler.END
    return await _show_stage(message, context, meta, prefix=t(meta["language"], "resumed"))


async def _answer(query) -> None:
    try:
        await query.answer()
    except Exception:
        logger.debug("Callback was already answered", exc_info=True)


async def on_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await _answer(query)
    code = query.data.split(":", 1)[1]
    if code not in LANGUAGES:
        return LANG
    context.user_data["lang"] = code
    await query.message.reply_text(
        t(code, "age_question"),
        reply_markup=_rows(
            [(t(code, "age_yes"), "gate:yes"), (t(code, "age_no"), "gate:no")],
        ),
    )
    return AGE_GATE


async def on_age_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await _answer(query)
    lang = _lang(context)
    choice = query.data.split(":", 1)[1]
    if choice != "yes":
        await query.message.reply_text(t(lang, "age_blocked"))
        return ConversationHandler.END
    await query.message.reply_text(
        t(lang, "policy"),
        reply_markup=_rows([(t(lang, "policy_agree"), "consent:yes")]),
    )
    return CONSENT


async def on_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await _answer(query)
    lang = _lang(context)
    if query.data != "consent:yes":
        await query.message.reply_text(t(lang, "use_buttons"))
        return CONSENT
    meta = _store(context).create(update.effective_user.id, lang)
    return await _show_stage(query.message, context, meta)


async def on_age_band(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await _answer(query)
    code = query.data.split(":", 1)[1]
    meta = _store(context).get(update.effective_user.id)
    lang = _lang(context, meta)
    if meta is None or code not in AGE_BANDS:
        await query.message.reply_text(t(lang, "use_buttons"))
        return AGE_BAND
    meta = _store(context).update(meta["participant_id"], age_band=code)
    return await _show_stage(query.message, context, meta)


async def on_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await _answer(query)
    code = query.data.split(":", 1)[1]
    meta = _store(context).get(update.effective_user.id)
    lang = _lang(context, meta)
    if meta is None or code not in REGIONS:
        await query.message.reply_text(t(lang, "use_buttons"))
        return REGION
    meta = _store(context).update(meta["participant_id"], region=code)
    return await _show_stage(query.message, context, meta)


async def on_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await _answer(query)
    code = query.data.split(":", 1)[1]
    meta = _store(context).get(update.effective_user.id)
    lang = _lang(context, meta)
    if meta is None or code not in GENDERS:
        await query.message.reply_text(t(lang, "use_buttons"))
        return GENDER
    meta = _store(context).update(meta["participant_id"], gender=code)
    return await _show_stage(query.message, context, meta)


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.effective_message
    meta = _store(context).get(update.effective_user.id)
    if meta is None:
        await message.reply_text(t(_lang(context), "help"))
        return ConversationHandler.END
    lang = _lang(context, meta)
    if stage(meta) != "photo":
        return await _show_stage(message, context, meta)

    image = _image_file(message)
    if image is None:
        await message.reply_text(t(lang, "send_photo"))
        return PHOTO
    if _is_forward(message):
        await message.reply_text(t(lang, "no_forward"))
        return PHOTO
    file_size = getattr(image, "file_size", None)
    if file_size and file_size > MAX_DOCUMENT_BYTES:
        await message.reply_text(t(lang, "too_big"))
        return PHOTO

    emotion, shot = next_request(meta)
    try:
        telegram_file = await image.get_file()
        payload = bytes(await telegram_file.download_as_bytearray())
        status, jpeg = inspect(payload)
        if status != "ok" or not jpeg:
            key = {"none": "no_face", "many": "many_faces"}.get(status, "bad_image")
            await message.reply_text(t(lang, key))
            return PHOTO
        meta = _store(context).save_photo(meta["participant_id"], emotion, shot, jpeg)
    except Exception:
        logger.exception("Could not save a photo for %s", meta["participant_id"])
        await message.reply_text(t(lang, "error"))
        return PHOTO
    saved = len(meta["photos"])
    logger.info("Saved %s %s shot %s (%s/%s)", meta["participant_id"], emotion, shot, saved, TOTAL_PHOTOS)
    prefix = t(lang, "accepted", saved=saved, total=TOTAL_PHOTOS)
    return await _show_stage(message, context, meta, prefix=prefix)


async def on_example(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await _answer(query)
    choice = query.data.split(":", 1)[1]
    meta = _store(context).get(update.effective_user.id)
    lang = _lang(context, meta)
    if meta is None or choice not in {"yes", "no"}:
        await query.message.reply_text(t(lang, "use_buttons"))
        return EXAMPLE
    meta = _store(context).update(meta["participant_id"], allow_example=(choice == "yes"))
    logger.info(
        "Completed %s allow_example=%s photos=%s",
        meta["participant_id"],
        meta["allow_example"],
        len(meta["photos"]),
    )
    return await _show_stage(query.message, context, meta)


async def on_example_nudge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    meta = _store(context).get(update.effective_user.id)
    lang = _lang(context, meta)
    await update.effective_message.reply_text(t(lang, "use_buttons"))
    return EXAMPLE


async def on_idle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Continue from disk if the process restarted and forgot the chat state."""
    message = update.effective_message
    user = update.effective_user
    meta = _store(context).get(user.id) if user else None
    if meta is None:
        await message.reply_text(t(_lang(context), "help"))
        return
    lang = meta["language"]
    if stage(meta) == "complete":
        await message.reply_text(
            t(lang, "already_done", participant_id=meta["participant_id"])
        )
        return
    if stage(meta) == "photo" and _image_file(message) is not None:
        await on_photo(update, context)
        return
    await _show_stage(message, context, meta, prefix=t(lang, "resumed"))


async def on_idle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    meta = _store(context).get(update.effective_user.id) if update.effective_user else None
    data = query.data or ""
    if meta is None:
        await _answer(query)
        await query.message.reply_text(t(_lang(context), "help"))
        return
    current = stage(meta)
    if current == "complete":
        await _answer(query)
        await query.message.reply_text(
            t(meta["language"], "already_done", participant_id=meta["participant_id"])
        )
        return
    if current == "age_band" and data.startswith("age:"):
        await on_age_band(update, context)
        return
    if current == "region" and data.startswith("reg:"):
        await on_region(update, context)
        return
    if current == "gender" and data.startswith("gen:"):
        await on_gender(update, context)
        return
    if current == "example" and data.startswith("ex:"):
        await on_example(update, context)
        return
    await _answer(query)
    await _show_stage(query.message, context, meta, prefix=t(meta["language"], "resumed"))


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    removed = _store(context).delete(update.effective_user.id)
    lang = _lang(context)
    context.user_data.clear()
    await update.effective_message.reply_text(t(lang, "deleted" if removed else "nothing_to_delete"))
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.reply_text(t(_lang(context), "cancelled"))
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    meta = _store(context).get(update.effective_user.id)
    await update.effective_message.reply_text(t(_lang(context, meta), "help"))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    owner = owner_id()
    user_id = update.effective_user.id
    if owner is None or user_id != owner:
        return
    report = _store(context).summary()
    lines = [
        f"Folder: {report['root']}",
        f"Complete: {report['complete']}",
        f"In progress: {report['partial']}",
        f"Photos: {report['photo_total']}",
    ]
    for emotion in EMOTIONS:
        lines.append(f"{emotion_label('en', emotion)}: {report['photos'][emotion]}")
    await update.effective_message.reply_text("\n".join(lines))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Update failed: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        lang = "uz"
        if update.effective_user:
            meta = _store(context).get(update.effective_user.id)
            lang = _lang(context, meta)
        try:
            await update.effective_message.reply_text(t(lang, "error"))
        except Exception:
            logger.exception("Could not send the error reply")


def build_application(token: str, store: DatasetStore) -> Application:
    application = Application.builder().token(token).build()
    application.bot_data["store"] = store

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start, filters=filters.ChatType.PRIVATE)],
        # Photos and buttons share one session per person. per_message would
        # track each button separately and cannot also accept photos.
        states={
            LANG: [CallbackQueryHandler(on_language, pattern=r"^lang:")],
            AGE_GATE: [CallbackQueryHandler(on_age_gate, pattern=r"^gate:")],
            CONSENT: [CallbackQueryHandler(on_consent, pattern=r"^consent:")],
            AGE_BAND: [CallbackQueryHandler(on_age_band, pattern=r"^age:")],
            REGION: [CallbackQueryHandler(on_region, pattern=r"^reg:")],
            GENDER: [CallbackQueryHandler(on_gender, pattern=r"^gen:")],
            PHOTO: [MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, on_photo)],
            EXAMPLE: [
                CallbackQueryHandler(on_example, pattern=r"^ex:"),
                MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, on_example_nudge),
            ],
        },
        fallbacks=[
            CommandHandler("delete", delete_command),
            CommandHandler("cancel", cancel_command),
            CommandHandler("help", help_command),
            CommandHandler("stats", stats_command),
        ],
        allow_reentry=True,
        per_chat=True,
        per_user=True,
        per_message=False,
        name="enroll",
    )
    application.add_handler(conversation)
    # These run only when a session is not already active. During a session the
    # conversation fallbacks handle the same commands and block this group.
    application.add_handler(CommandHandler("delete", delete_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("help", help_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("stats", stats_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, on_idle_message))
    application.add_handler(CallbackQueryHandler(on_idle_callback))
    application.add_error_handler(on_error)
    return application
