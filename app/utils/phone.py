import re

PHONE_PATTERN = re.compile(r"^\+?[0-9]{10,15}$")


def is_valid_phone(phone: str) -> bool:
    cleaned = re.sub(r"[\s\-()]", "", phone.strip())
    return bool(PHONE_PATTERN.match(cleaned))


def normalize_phone_digits(phone: str) -> str:
    """Return digits only for consistent phone matching."""
    return re.sub(r"\D", "", (phone or "").strip())


def phone_match_suffix(phone: str) -> str:
    """Last 10 digits — used to match orders across +91 / 0 prefixes."""
    digits = normalize_phone_digits(phone)
    return digits[-10:] if len(digits) >= 10 else digits


def phones_match(phone_a: str, phone_b: str) -> bool:
    """True when two numbers share the same 10-digit mobile identity."""
    suffix_a = phone_match_suffix(phone_a)
    suffix_b = phone_match_suffix(phone_b)
    return bool(suffix_a) and len(suffix_a) >= 10 and suffix_a == suffix_b
