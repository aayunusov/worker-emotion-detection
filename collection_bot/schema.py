"""Shared constants for the posed-face collection."""

POLICY_VERSION = "1"

EMOTIONS = (
    "neutral",
    "happy",
    "sad",
    "angry",
    "surprise",
    "fear",
    "disgust",
)

SHOTS_PER_EMOTION = 2
TOTAL_PHOTOS = len(EMOTIONS) * SHOTS_PER_EMOTION

AGE_BANDS = ("18-24", "25-34", "35-44", "45+", "prefer_not")
GENDERS = ("female", "male", "prefer_not")

# Codes are stable. Labels live in texts.py.
REGIONS = (
    "toshkent_shahri",
    "toshkent_viloyati",
    "andijon",
    "buxoro",
    "fargona",
    "jizzax",
    "qashqadaryo",
    "navoiy",
    "namangan",
    "samarqand",
    "surxondaryo",
    "sirdaryo",
    "xorazm",
    "qoraqalpogiston",
    "other",
    "prefer_not",
)

LANGUAGES = ("uz", "ru", "en")
