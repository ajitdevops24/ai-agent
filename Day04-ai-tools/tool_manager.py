from tools import (
    get_current_time,
    roll_dice,
    generate_password
)
'''
def execute_tool(user_input):

    text = user_input.lower()

    if "time" in text or "clock" in text:
        return get_current_time()

    if "dice" in text or "die" in text:
        return f"You rolled {roll_dice()}"

    if "password" in text:
        return generate_password()

    return None
'''
import re

def has_word(text, words):
    return any(re.search(rf"\b{w}\b", text) for w in words)

def execute_tool(user_input):
    text = user_input.lower()

    if has_word(text, ["time", "clock"]):
        return get_current_time()
    if has_word(text, ["dice", "die"]):
        return f"You rolled {roll_dice()}"
    if has_word(text, ["password"]) and has_word(text, ["generate", "give", "create", "new"]):
        return generate_password()
    return None