"""User-facing copy in Uzbek, Russian, and English."""

from __future__ import annotations

from collection_bot.schema import EMOTIONS, LANGUAGES, REGIONS

TEXTS: dict[str, dict[str, str]] = {
    "uz": {
        "private_only": "Bu bot faqat shaxsiy chatda ishlaydi. Menga shu yerdan yozing.",
        "choose_language": "Tilni tanlang.\nВыберите язык.\nChoose a language.",
        "age_question": "Bu tadqiqot faqat 18 yoshga to‘lganlar uchun.\nSiz 18 yoshga to‘lganmisiz?",
        "age_yes": "Ha, 18 yoshdaman",
        "age_no": "Yo‘q",
        "age_blocked": "Rahmat. Ishtirok etish uchun 18 yoshga to‘lgan bo‘lish kerak.",
        "policy": (
            "Ma’lumotlar siyosati (1-versiya)\n\n"
            "Bu bot magistrlik dissertatsiyasi uchun yuz rasmlarini yig‘adi. "
            "Mavzu: yuz ifodasi bo‘yicha emotsiyani aniqlash.\n\n"
            "Sizdan 7 ta ifoda so‘raladi, har biridan 2 ta yangi rasm. "
            "Rasm yorlig‘i — bot so‘ragan ifoda.\n\n"
            "Saqlanadi: rasmlar, yosh oralig‘i, hudud, jins (agar aytsangiz) "
            "va Telegram id (o‘chirish uchun). Ism so‘ralmaydi.\n\n"
            "Ishtirok ixtiyoriy va bahoga ta’sir qilmaydi.\n\n"
            "/delete yuborsangiz, rasmlaringiz kompyuterdagi papkadan o‘chiriladi.\n\n"
            "Rasmlar Telegram serverlari orqali o‘tadi. Saqlangan faylda telefon joylashuvi qolmaydi.\n\n"
            "Dissertatsiyada rasmingiz faqat oxiridagi alohida savolga rozilik bersangiz chiqadi.\n\n"
            "Davom etish uchun «Roziman» ni bosing."
        ),
        "policy_agree": "Roziman",
        "ask_age_band": "Yosh oralig‘ingizni tanlang.",
        "ask_region": "Qaysi hududdansiz?",
        "ask_gender": "Jinsingiz (ixtiyoriy).",
        "prefer_not": "Aytmayman",
        "female": "Ayol",
        "male": "Erkak",
        "photo_prompt": (
            "{label}\n\n"
            "{hint}\n\n"
            "Shu ifoda uchun yangi rasm: {shot}/2.\n"
            "Saqlangan rasmlar: {saved}/{total}.\n\n"
            "Kameraga qarang. Kadrda bitta odam bo‘lsin, yuz ochiq ko‘rinsin. "
            "Eski rasm yoki forward yubormang."
        ),
        "accepted": "Qabul qilindi ({saved}/{total}).",
        "send_photo": "Iltimos, matn emas, yangi rasm yuboring.",
        "no_forward": "Forward qabul qilinmaydi. Kameradan hozir tushgan rasmni yuboring.",
        "no_face": "Yuz topilmadi. Yuzingiz yorug‘ joyda, kameraga yaqinroq tursin va qayta yuboring.",
        "many_faces": "Bir nechta yuz ko‘rindi. Kadrda faqat o‘zingiz bo‘ling va qayta yuboring.",
        "bad_image": "Bu rasmni o‘qib bo‘lmadi. Boshqa rasm yuboring.",
        "too_big": "Rasm juda katta. Oddiy kamera rasmi sifatida qayta yuboring.",
        "ask_example": (
            "Dissertatsiyada bitta rasmingiz namuna sifatida chiqishi mumkinmi?\n"
            "Bu ixtiyoriy. «Yo‘q» desangiz ham rasmlar tadqiqotda ishlatiladi, lekin chop etilmaydi."
        ),
        "example_yes": "Ha, namuna bo‘lishi mumkin",
        "example_no": "Yo‘q, chop etmang",
        "thanks": (
            "Rahmat, ishtirokingiz uchun.\n"
            "{count} ta rasm saqlandi. Sizning raqamingiz: {participant_id}.\n"
            "O‘chirish uchun istalgan payt /delete yuboring."
        ),
        "already_done": "Siz allaqachon qatnashgansiz ({participant_id}). Qayta yuborish uchun avval /delete yuboring.",
        "resumed": "Davom etamiz. Qolgan qadam shu yerda.",
        "deleted": "Ma’lumotlaringiz o‘chirildi. Qayta boshlash uchun /start yuboring.",
        "nothing_to_delete": "O‘chiriladigan ma’lumot topilmadi.",
        "cancelled": "To‘xtatildi. Yuborilgan rasmlar saqlanib turibdi. Davom etish: /start. O‘chirish: /delete.",
        "use_buttons": "Pastdagi tugmalardan birini bosing.",
        "help": "/start — boshlash yoki davom etish\n/delete — rasmlaringizni o‘chirish\n/cancel — hozircha to‘xtatish",
        "error": "Xatolik yuz berdi. Iltimos, rasmni qayta yuboring yoki /start ni bosing.",
    },
    "ru": {
        "private_only": "Бот работает только в личном чате. Напишите ему напрямую.",
        "choose_language": "Tilni tanlang.\nВыберите язык.\nChoose a language.",
        "age_question": "В исследовании могут участвовать только люди старше 18 лет.\nВам уже есть 18?",
        "age_yes": "Да, мне есть 18",
        "age_no": "Нет",
        "age_blocked": "Спасибо. Участвовать можно только с 18 лет.",
        "policy": (
            "Политика данных (версия 1)\n\n"
            "Этот бот собирает фотографии лица для магистерской диссертации "
            "по классификации эмоций по выражению лица.\n\n"
            "Нужно показать 7 выражений и прислать по 2 новых фото на каждое. "
            "Метка фото — выражение, которое попросил бот.\n\n"
            "Сохраняется: фото, возрастная группа, регион, пол (если укажете) "
            "и Telegram id, чтобы можно было удалить данные. Имя не спрашивается.\n\n"
            "Участие добровольное и не влияет на оценки.\n\n"
            "Команда /delete удаляет вашу папку с компьютера, где хранится сбор.\n\n"
            "Фото проходят через серверы Telegram. В сохранённом файле не остаётся геолокация телефона.\n\n"
            "В диссертации фото появится только если вы отдельно разрешите это в конце.\n\n"
            "Нажмите «Соглашаюсь», чтобы продолжить."
        ),
        "policy_agree": "Соглашаюсь",
        "ask_age_band": "Выберите возрастную группу.",
        "ask_region": "Из какого вы региона?",
        "ask_gender": "Пол (необязательно).",
        "prefer_not": "Не указывать",
        "female": "Женский",
        "male": "Мужской",
        "photo_prompt": (
            "{label}\n\n"
            "{hint}\n\n"
            "Новое фото для этого выражения: {shot}/2.\n"
            "Уже сохранено: {saved}/{total}.\n\n"
            "Смотрите в камеру. В кадре только вы, лицо хорошо видно. "
            "Не присылайте старое фото и не пересылайте чужое."
        ),
        "accepted": "Принято ({saved}/{total}).",
        "send_photo": "Пришлите новое фото, а не текст.",
        "no_forward": "Пересланные фото не принимаются. Снимите новое на камеру.",
        "no_face": "Лицо не найдено. Встаньте ближе к камере при хорошем свете и пришлите снова.",
        "many_faces": "В кадре несколько лиц. Оставьте в кадре только себя и пришлите снова.",
        "bad_image": "Не удалось прочитать фото. Пришлите другое.",
        "too_big": "Файл слишком большой. Пришлите обычное фото с камеры.",
        "ask_example": (
            "Можно показать одно ваше фото как пример в диссертации?\n"
            "Это необязательно. Если ответите «нет», фото останутся в исследовании, но не будут опубликованы."
        ),
        "example_yes": "Да, можно показать пример",
        "example_no": "Нет, не публиковать",
        "thanks": (
            "Спасибо за участие.\n"
            "Сохранено фото: {count}. Ваш номер: {participant_id}.\n"
            "Удалить данные в любой момент: /delete."
        ),
        "already_done": "Вы уже участвовали ({participant_id}). Чтобы пройти заново, сначала отправьте /delete.",
        "resumed": "Продолжаем с того места, где остановились.",
        "deleted": "Ваши данные удалены. Чтобы начать снова, отправьте /start.",
        "nothing_to_delete": "Удалять нечего.",
        "cancelled": "Пауза. Уже присланные фото сохранены. Продолжить: /start. Удалить: /delete.",
        "use_buttons": "Нажмите одну из кнопок ниже.",
        "help": "/start — начать или продолжить\n/delete — удалить ваши фото\n/cancel — поставить на паузу",
        "error": "Произошла ошибка. Пришлите фото ещё раз или нажмите /start.",
    },
    "en": {
        "private_only": "This bot only works in a private chat. Message it directly.",
        "choose_language": "Tilni tanlang.\nВыберите язык.\nChoose a language.",
        "age_question": "This study is only for people who are 18 or older.\nAre you 18 or older?",
        "age_yes": "Yes, I am 18 or older",
        "age_no": "No",
        "age_blocked": "Thank you. Only people who are 18 or older can take part.",
        "policy": (
            "Data policy (version 1)\n\n"
            "This bot collects face photos for a master's thesis on classifying emotion from facial images.\n\n"
            "You will pose 7 expressions and send 2 new photos of each. "
            "The label of a photo is the expression the bot asked for.\n\n"
            "What is stored: the photos, your age band, your region, your gender if you choose to give it, "
            "and your Telegram id so you can delete the data. Your name is not asked.\n\n"
            "Participation is voluntary and does not affect grades.\n\n"
            "Send /delete at any time and your folder will be removed from the computer that stores the collection.\n\n"
            "Photos also pass through Telegram's servers, because that is how this chat works. "
            "Saved files do not keep phone location data.\n\n"
            "A photo of you appears in the thesis only if you allow it in a separate question at the end.\n\n"
            "Tap “I agree” to continue."
        ),
        "policy_agree": "I agree",
        "ask_age_band": "Choose your age band.",
        "ask_region": "Which region are you from?",
        "ask_gender": "Gender (optional).",
        "prefer_not": "Prefer not to say",
        "female": "Female",
        "male": "Male",
        "photo_prompt": (
            "{label}\n\n"
            "{hint}\n\n"
            "New photo for this expression: {shot}/2.\n"
            "Photos saved: {saved}/{total}.\n\n"
            "Look at the camera. Only you in the frame, face clearly visible. "
            "Do not send an old photo or a forward."
        ),
        "accepted": "Saved ({saved}/{total}).",
        "send_photo": "Please send a new photo, not text.",
        "no_forward": "Forwarded photos are not accepted. Take a new one with the camera.",
        "no_face": "No face found. Move closer, use better light, and send the photo again.",
        "many_faces": "More than one face was found. Be alone in the frame and send it again.",
        "bad_image": "That image could not be read. Please send another photo.",
        "too_big": "That file is too large. Send a normal camera photo.",
        "ask_example": (
            "May one of your photos be printed as an example in the thesis?\n"
            "This is optional. If you say no, the photos still stay in the study, but they will not be published."
        ),
        "example_yes": "Yes, an example is fine",
        "example_no": "No, do not publish",
        "thanks": (
            "Thank you for taking part.\n"
            "{count} photos were saved. Your id is {participant_id}.\n"
            "Send /delete at any time to remove your data."
        ),
        "already_done": "You already finished ({participant_id}). Send /delete first if you want to start again.",
        "resumed": "Continuing from where you stopped.",
        "deleted": "Your data has been deleted. Send /start to begin again.",
        "nothing_to_delete": "There is nothing to delete.",
        "cancelled": "Paused. Photos you already sent are kept. Continue with /start. Delete with /delete.",
        "use_buttons": "Tap one of the buttons below.",
        "help": "/start — start or resume\n/delete — delete your photos\n/cancel — pause",
        "error": "Something went wrong. Send the photo again, or tap /start.",
    },
}

EMOTION_LABELS: dict[str, dict[str, str]] = {
    "uz": {
        "neutral": "Neytral",
        "happy": "Xursand",
        "sad": "Xafa",
        "angry": "Jahldor",
        "surprise": "Hayron",
        "fear": "Qo‘rquv",
        "disgust": "Jirkanish",
    },
    "ru": {
        "neutral": "Нейтральное",
        "happy": "Радость",
        "sad": "Грусть",
        "angry": "Злость",
        "surprise": "Удивление",
        "fear": "Страх",
        "disgust": "Отвращение",
    },
    "en": {
        "neutral": "Neutral",
        "happy": "Happy",
        "sad": "Sad",
        "angry": "Angry",
        "surprise": "Surprise",
        "fear": "Fear",
        "disgust": "Disgust",
    },
}

EMOTION_HINTS: dict[str, dict[str, str]] = {
    "uz": {
        "neutral": "Oddiy yuz. Tabassum qilmang, og‘iz yumiq.",
        "happy": "Tabassum qiling, xuddi suratga tushayotgandek.",
        "sad": "Xafa ifoda. Og‘iz burchaklari pastga.",
        "angry": "Jahldor ifoda. Qoshlar pastga, jag‘ tarang.",
        "surprise": "Hayron qoling: qoshlar yuqoriga, og‘iz biroz ochiq.",
        "fear": "Qo‘rqqan ifoda: ko‘zlar keng, og‘iz biroz ochiq.",
        "disgust": "Burunni tirishtiring, xuddi yomon hid sezgandek.",
    },
    "ru": {
        "neutral": "Обычное лицо. Не улыбайтесь, рот закрыт.",
        "happy": "Улыбнитесь, как для обычного фото.",
        "sad": "Грустное лицо. Уголки рта опущены.",
        "angry": "Злое лицо. Брови опущены, челюсть напряжена.",
        "surprise": "Удивление: брови вверх, рот немного открыт.",
        "fear": "Испуг: глаза широко открыты, рот немного открыт.",
        "disgust": "Сморщите нос, как будто неприятный запах.",
    },
    "en": {
        "neutral": "Resting face. Do not smile. Mouth closed.",
        "happy": "Smile, as you would for a normal photo.",
        "sad": "A sad face. Corners of the mouth down.",
        "angry": "An angry face. Brows down, jaw tense.",
        "surprise": "Look surprised: brows up, mouth slightly open.",
        "fear": "A frightened face: eyes wide, mouth slightly open.",
        "disgust": "Wrinkle your nose, as if something smells bad.",
    },
}

REGION_LABELS: dict[str, dict[str, str]] = {
    "uz": {
        "toshkent_shahri": "Toshkent shahri",
        "toshkent_viloyati": "Toshkent viloyati",
        "andijon": "Andijon",
        "buxoro": "Buxoro",
        "fargona": "Farg‘ona",
        "jizzax": "Jizzax",
        "qashqadaryo": "Qashqadaryo",
        "navoiy": "Navoiy",
        "namangan": "Namangan",
        "samarqand": "Samarqand",
        "surxondaryo": "Surxondaryo",
        "sirdaryo": "Sirdaryo",
        "xorazm": "Xorazm",
        "qoraqalpogiston": "Qoraqalpog‘iston",
        "other": "Boshqa",
        "prefer_not": "Aytmayman",
    },
    "ru": {
        "toshkent_shahri": "город Ташкент",
        "toshkent_viloyati": "Ташкентская область",
        "andijon": "Андижан",
        "buxoro": "Бухара",
        "fargona": "Фергана",
        "jizzax": "Джизак",
        "qashqadaryo": "Кашкадарья",
        "navoiy": "Навои",
        "namangan": "Наманган",
        "samarqand": "Самарканд",
        "surxondaryo": "Сурхандарья",
        "sirdaryo": "Сырдарья",
        "xorazm": "Хорезм",
        "qoraqalpogiston": "Каракалпакстан",
        "other": "Другое",
        "prefer_not": "Не указывать",
    },
    "en": {
        "toshkent_shahri": "Tashkent city",
        "toshkent_viloyati": "Tashkent region",
        "andijon": "Andijan",
        "buxoro": "Bukhara",
        "fargona": "Fergana",
        "jizzax": "Jizzakh",
        "qashqadaryo": "Kashkadarya",
        "navoiy": "Navoi",
        "namangan": "Namangan",
        "samarqand": "Samarkand",
        "surxondaryo": "Surkhandarya",
        "sirdaryo": "Syrdarya",
        "xorazm": "Khorezm",
        "qoraqalpogiston": "Karakalpakstan",
        "other": "Other",
        "prefer_not": "Prefer not to say",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    table = TEXTS.get(lang) or TEXTS["en"]
    template = table.get(key) or TEXTS["en"][key]
    return template.format(**kwargs)


def emotion_label(lang: str, emotion: str) -> str:
    table = EMOTION_LABELS.get(lang) or EMOTION_LABELS["en"]
    return table[emotion]


def emotion_hint(lang: str, emotion: str) -> str:
    table = EMOTION_HINTS.get(lang) or EMOTION_HINTS["en"]
    return table[emotion]


def region_label(lang: str, code: str) -> str:
    table = REGION_LABELS.get(lang) or REGION_LABELS["en"]
    return table[code]


def photo_prompt(lang: str, emotion: str, shot: int, saved: int, total: int) -> str:
    return t(
        lang,
        "photo_prompt",
        label=emotion_label(lang, emotion),
        hint=emotion_hint(lang, emotion),
        shot=shot,
        saved=saved,
        total=total,
    )


def covered() -> bool:
    """True when every language has the same keys, emotions, and regions."""
    keys = set(TEXTS["en"])
    for lang in LANGUAGES:
        if set(TEXTS[lang]) != keys:
            return False
        if set(EMOTION_LABELS[lang]) != set(EMOTIONS):
            return False
        if set(EMOTION_HINTS[lang]) != set(EMOTIONS):
            return False
        if set(REGION_LABELS[lang]) != set(REGIONS):
            return False
    return True
