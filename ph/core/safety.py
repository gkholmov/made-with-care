"""Code-enforced safety gate. Runs on EVERY inbound message, independent of the LLM.

If a message matches a high-risk pattern (money movement, sharing codes, granting
remote access, authority-impersonation, or bank/financial account access), the
orchestrator forces a `safety_stop`: it tells the elder to stop, and notifies the
relative. The LLM can never override this.
"""
from __future__ import annotations
import re

# High-risk signals (multilingual). Lowercased substring / word matching.
_SCAM_TERMS = [
    # money movement
    "gift card", "google play card", "itunes card", "steam card", "wire transfer",
    "send money", "transfer money", "western union", "bitcoin", "crypto", "btc", "usdt",
    "pay the fee", "processing fee", "buy a card",
    # codes / credentials being requested by someone
    "send the code", "give the code", "read me the code", "verification code", "one-time code",
    "tell me your password", "share your password", "give your password",
    # remote access
    "anydesk", "teamviewer", "remote access", "let me access your computer", "install this so i can",
    # authority impersonation
    "federal agent", "irs", "social security office", "police said", "arrest", "customs",
    "your account is suspended", "your computer is infected", "microsoft support called",
    # ru
    "подарочная карта", "перевести деньги", "перевод денег", "отправить деньги", "биткоин",
    "криптовалюта", "код из смс", "назовите код", "продиктуйте код", "скажите пароль",
    "удалённый доступ", "теамвивер", "энидеск", "налоговая", "полиция", "счёт заблокирован",
    "ваш компьютер заражён", "оплатите комиссию",
    # de
    "gutschein", "geld überweisen", "geld senden", "überweisung", "bitcoin", "krypto",
    "code aus der sms", "sag mir den code", "passwort sagen", "fernzugriff", "teamviewer",
    "finanzamt", "polizei", "konto gesperrt", "ihr computer ist infiziert", "gebühr zahlen",
]

# Bank / financial account access -> hand to relative (don't guide alone).
_FINANCIAL_TERMS = [
    "bank account", "online banking", "bank login", "bank password", "credit card", "debit card",
    "paypal password", "investment account", "pension account",
    "банк", "онлайн-банк", "пароль от банка", "кредитная карта", "карта сбербанк", "пэйпал",
    "bankkonto", "online-banking", "bank-passwort", "kreditkarte", "paypal-passwort",
]


def _hit(text: str, terms) -> bool:
    low = (text or "").lower()
    return any(term in low for term in terms)


def classify(text: str) -> str:
    """Return 'scam' | 'financial' | 'safe'. Non-safe -> safety_stop + escalate."""
    if _hit(text, _SCAM_TERMS):
        return "scam"
    if _hit(text, _FINANCIAL_TERMS):
        return "financial"
    return "safe"


def is_safe(text: str) -> bool:
    return classify(text) == "safe"
