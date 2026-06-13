"""Curated scenario playbooks — the source of truth for tech steps.

The AI rephrases these; it does not invent procedures. Each step's `instruction`
is canonical English. `check=True` means "if the elder says it worked, we're done".
`on_exhaust` decides what happens after the last step ('escalate' or 'resolved').
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Step:
    instruction: str
    check: bool = False


@dataclass
class Playbook:
    name: str
    on_exhaust: str            # 'escalate' | 'resolved'
    steps: list = field(default_factory=list)
    flag_event: str = ""        # optional event to log on entry (e.g. 'scam_flag')


WIFI = Playbook(
    name="wifi", on_exhaust="escalate",
    steps=[
        Step("Let's fix your internet together. First, look at the very top of your screen — "
             "do you see the little fan-shaped wifi symbol? Tell me yes or no, or send a photo.", check=True),
        Step("Let's restart your internet box. Find the small box with blinking lights, gently unplug "
             "its power cord, wait while you count slowly to 30, then plug it back in. "
             "Tell me when the lights stop blinking and stay steady.", check=True),
        Step("Now let's reconnect. Open your wifi settings and tap your home network name. If it asks for "
             "the wifi password, it's the one written on the box or on your note — don't tell it to me. "
             "Did it connect?", check=True),
    ],
)

PASSWORD = Playbook(
    name="password", on_exhaust="escalate",
    steps=[
        Step("Let's get you back into your account. Which one is it — your email, your Apple account, or "
             "your Google account? (Anything to do with your bank, we'll get your relative — I can't help "
             "with bank logins.)"),
        Step("Good. On the sign-in screen, tap the small words that say 'Forgot password?'. "
             "Tell me when you see a box to type your email."),
        Step("Type your email address and tap Continue. They will send a reset link to your email or a text. "
             "Open it and pick a NEW password you'll remember. Never read any code out loud or type it to me."),
        Step("Type your new password (twice if it asks) and save. Now try to sign in. Did it work?", check=True),
    ],
)

OS_UPDATE = Playbook(
    name="os_update", on_exhaust="resolved",
    steps=[
        Step("Your phone just updated — nothing is broken, it only looks a little different. "
             "What can't you find? For example your Phone, your Messages, or your Camera?"),
        Step("It's still there, just moved. Swipe slowly from the middle of the screen downward, then type "
             "the first letters of what you want — like 'Phone'. Tap it when it appears. Did you find it?", check=True),
        Step("Lovely. If you'd like, press and hold its icon and drag it to your first screen so it's easy to "
             "find next time. Tell me when it's where you like it.", check=True),
    ],
)

SETUP = Playbook(
    name="setup", on_exhaust="resolved",
    steps=[
        Step("Happy to help. The easiest improvement is bigger text. Do you have an iPhone or an Android "
             "phone? (Or just send me a photo of your screen.)"),
        Step("Let's make the words bigger. On iPhone: open Settings → 'Display & Brightness' → 'Text Size' "
             "and drag the slider right. On Android: open Settings → 'Display' → 'Font size' and drag it "
             "right. Tell me when the words look comfortable.", check=True),
        Step("Wonderful. Would you like me to help put Phone, Messages and Camera on your first screen so "
             "they're always easy to find?", check=True),
    ],
)

SCAM = Playbook(
    name="scam", on_exhaust="escalate", flag_event="scam_flag",
    steps=[
        Step("You did exactly the right thing by checking with me first. Read me what the message says, or "
             "send a photo of it. Remember: real banks and the government will NEVER ask for codes, passwords, "
             "or payment by gift card."),
        Step("Here is the safe rule, please follow it: do NOT click any links, do NOT call the number in the "
             "message, do NOT share any code or password, and do NOT send money or gift cards. If it claims to "
             "be your bank, hang up and call the number printed on your bank card. I'll let your relative know "
             "so you can double-check with them."),
    ],
)

REGISTRY = {p.name: p for p in [WIFI, PASSWORD, OS_UPDATE, SETUP, SCAM]}


def get(name: str) -> Playbook | None:
    return REGISTRY.get(name)
