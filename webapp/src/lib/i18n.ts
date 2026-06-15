/** Webapp-only strings (en/ru/de). Topic/button labels for the elder face come
 * from the API (single source of truth: ph/core/i18n.py) — this dict holds only
 * strings that exist purely in the Mini App. */

export type Lang = "en" | "ru" | "de";

const STR: Record<string, Record<Lang, string>> = {
  hello: { en: "Hello", ru: "Здравствуйте", de: "Hallo" },
  what_help: {
    en: "What do you need help with?",
    ru: "С чем вам помочь?",
    de: "Wobei kann ich helfen?",
  },
  show_screen: {
    en: "Show my screen",
    ru: "Показать экран",
    de: "Bildschirm zeigen",
  },
  call: { en: "Call", ru: "Позвонить", de: "Anrufen" },
  typing: { en: "Typing…", ru: "Печатает…", de: "Schreibt…" },
  type_here: {
    en: "Type your answer",
    ru: "Напишите ответ",
    de: "Antwort eingeben",
  },
  send: { en: "Send", ru: "Отправить", de: "Senden" },
  conf_worked: {
    en: "It worked",
    ru: "Получилось",
    de: "Hat geklappt",
  },
  conf_not_yet: { en: "Not yet", ru: "Пока нет", de: "Noch nicht" },
  photo_hint: {
    en: "📷 Show me your screen",
    ru: "📷 Покажите экран",
    de: "📷 Bildschirm zeigen",
  },
  conv_photo_sent: {
    en: "Photo sent",
    ru: "Фото отправлено",
    de: "Foto gesendet",
  },
  back_home: {
    en: "Back to topics",
    ru: "К списку тем",
    de: "Zurück zu den Themen",
  },
  conv_error: {
    en: "Hmm, please try again.",
    ru: "Хм, попробуйте ещё раз.",
    de: "Bitte erneut versuchen.",
  },
  done_title: { en: "All done! 🎉", ru: "Готово! 🎉", de: "Fertig! 🎉" },
  tell_problem: {
    en: "🎙️ Tell me the problem",
    ru: "🎙️ Расскажите, что случилось",
    de: "🎙️ Sagen Sie, was los ist",
  },
  recording: {
    en: "Recording… tap to send",
    ru: "Запись… нажмите, чтобы отправить",
    de: "Aufnahme… tippen zum Senden",
  },
  mic_error: {
    en: "I couldn't use the microphone. Please allow it, or type instead.",
    ru: "Не удалось включить микрофон. Разрешите доступ или напишите текстом.",
    de: "Mikrofon nicht verfügbar. Bitte erlauben oder tippen.",
  },
  transcribing: { en: "Listening…", ru: "Слушаю…", de: "Höre zu…" },
  continue_chat: {
    en: "Where we left off",
    ru: "С того места, где остановились",
    de: "Wo wir aufgehört haben",
  },
  gallery: {
    en: "🖼️ Choose a photo",
    ru: "🖼️ Выбрать фото",
    de: "🖼️ Foto auswählen",
  },
  how_help: {
    en: "How can I help today?",
    ru: "Чем я могу помочь?",
    de: "Wie kann ich heute helfen?",
  },
  show_my_screen: {
    en: "📷 Show my screen",
    ru: "📷 Показать мой экран",
    de: "📷 Meinen Bildschirm zeigen",
  },
  pick_problem: {
    en: "Or tap what's wrong:",
    ru: "Или нажмите, что не так:",
    de: "Oder tippen Sie an, was nicht stimmt:",
  },
  call_family: {
    en: "📞 Call my family",
    ru: "📞 Позвонить близким",
    de: "📞 Familie anrufen",
  },
  first_run_hint: {
    en: "Tap the blue button to talk to me, or tap your problem below. You can't break anything.",
    ru: "Нажмите синюю кнопку, чтобы поговорить со мной, или выберите проблему ниже. Вы ничего не сломаете.",
    de: "Tippen Sie auf die blaue Taste, um mit mir zu sprechen, oder wählen Sie unten Ihr Problem. Sie können nichts kaputt machen.",
  },
  other_ways: {
    en: "Other ways to answer:",
    ru: "Другие способы ответить:",
    de: "Andere Möglichkeiten zu antworten:",
  },
  talk: { en: "🎙️ Talk", ru: "🎙️ Сказать", de: "🎙️ Sprechen" },
  show: { en: "📷 Show", ru: "📷 Показать", de: "📷 Zeigen" },
  type_btn: { en: "⌨️ Type", ru: "⌨️ Печатать", de: "⌨️ Tippen" },
  status_sending_photo: {
    en: "Sending your photo…",
    ru: "Отправляю ваше фото…",
    de: "Sende Ihr Foto…",
  },
  status_thinking: { en: "Thinking…", ru: "Думаю…", de: "Überlege…" },
  // --- "Calm & Editorial" screens (emoji-free; icons are inline SVG) ---
  talk_to_me: {
    en: "Talk to me",
    ru: "Поговорите со мной",
    de: "Sprechen Sie mit mir",
  },
  problems_heading: {
    en: "Common problems",
    ru: "Частые проблемы",
    de: "Häufige Probleme",
  },
  continue_label: { en: "Continue", ru: "Продолжить", de: "Weiter" },
  helping_with: { en: "Helping with", ru: "Помогаю с", de: "Hilfe bei" },
  did_it_work: {
    en: "Did it work?",
    ru: "Получилось?",
    de: "Hat es geklappt?",
  },
  worked_plain: {
    en: "It worked",
    ru: "Получилось",
    de: "Hat geklappt",
  },
  not_yet_plain: { en: "Not yet", ru: "Пока нет", de: "Noch nicht" },
  talk_word: { en: "Talk", ru: "Сказать", de: "Sprechen" },
  show_word: { en: "Show", ru: "Показать", de: "Zeigen" },
  type_word: { en: "Type", ru: "Печатать", de: "Tippen" },
  resolved_title: {
    en: "All fixed. Well done.",
    ru: "Всё готово. Отлично.",
    de: "Alles erledigt. Gut gemacht.",
  },
  back_to_topics: {
    en: "Back to my topics",
    ru: "К моим темам",
    de: "Zurück zu meinen Themen",
  },
  escalated_title: {
    en: "Let's get a person to help",
    ru: "Давайте позовём человека",
    de: "Holen wir eine Person dazu",
  },
  connect_with: {
    en: "I'll connect you with",
    ru: "Я свяжу вас с",
    de: "Ich verbinde Sie mit",
  },
  call_now: {
    en: "Call now",
    ru: "Позвонить сейчас",
    de: "Jetzt anrufen",
  },
  dashboard: {
    en: "Family dashboard",
    ru: "Семейная панель",
    de: "Familien-Übersicht",
  },
  your_elders: {
    en: "Your relatives",
    ru: "Ваши близкие",
    de: "Ihre Angehörigen",
  },
  add_elder: {
    en: "Set up help for a relative",
    ru: "Настроить помощь для близкого",
    de: "Hilfe für Angehörige einrichten",
  },
  alerts: { en: "alerts", ru: "уведомл.", de: "Warnungen" },
  not_claimed: {
    en: "Link not opened yet",
    ru: "Ссылка ещё не открыта",
    de: "Link noch nicht geöffnet",
  },
  recent_activity: {
    en: "Recent activity",
    ru: "Недавняя активность",
    de: "Letzte Aktivität",
  },
  sessions: {
    en: "Help sessions",
    ru: "Обращения за помощью",
    de: "Hilfe-Sitzungen",
  },
  no_activity: {
    en: "No activity yet.",
    ru: "Пока нет активности.",
    de: "Noch keine Aktivität.",
  },
  settings: { en: "Settings", ru: "Настройки", de: "Einstellungen" },
  language: { en: "Language", ru: "Язык", de: "Sprache" },
  phone: { en: "Phone", ru: "Телефон", de: "Handy" },
  phone_age: {
    en: "Phone age",
    ru: "Возраст телефона",
    de: "Alter des Handys",
  },
  save: { en: "Save", ru: "Сохранить", de: "Speichern" },
  saved: { en: "Saved ✓", ru: "Сохранено ✓", de: "Gespeichert ✓" },
  share_link: {
    en: "Share the link",
    ru: "Отправить ссылку",
    de: "Link teilen",
  },
  join_link_hint: {
    en: "Send this personal link to your relative — when they tap it, the helper introduces itself.",
    ru: "Отправьте эту личную ссылку близкому — когда они её откроют, помощник представится.",
    de: "Senden Sie diesen persönlichen Link an Ihren Angehörigen — beim Öffnen stellt sich der Helfer vor.",
  },
  wizard_title: {
    en: "Set up the helper",
    ru: "Настройка помощника",
    de: "Helfer einrichten",
  },
  w_name: {
    en: "Your relative's first name",
    ru: "Имя вашего близкого",
    de: "Vorname Ihres Angehörigen",
  },
  w_lang: {
    en: "Which language should the helper speak?",
    ru: "На каком языке говорить помощнику?",
    de: "Welche Sprache soll der Helfer sprechen?",
  },
  w_os: {
    en: "What phone do they have?",
    ru: "Какой у них телефон?",
    de: "Welches Handy haben sie?",
  },
  w_age: {
    en: "Is it fairly new or quite old?",
    ru: "Он новый или старый?",
    de: "Ist es eher neu oder alt?",
  },
  w_email: {
    en: "Your email for urgent alerts (optional)",
    ru: "Ваш email для срочных уведомлений (необязательно)",
    de: "Ihre E-Mail für dringende Warnungen (optional)",
  },
  w_new: { en: "New", ru: "Новый", de: "Neu" },
  w_old: { en: "Old", ru: "Старый", de: "Alt" },
  create_link: {
    en: "Create the link",
    ru: "Создать ссылку",
    de: "Link erstellen",
  },
  unknown_title: {
    en: "This helper is set up by family",
    ru: "Помощника настраивают близкие",
    de: "Dieser Helfer wird von der Familie eingerichtet",
  },
  unknown_body: {
    en: "If your family set this up for you, please open the personal link they sent you.",
    ru: "Если близкие настроили помощника для вас, откройте личную ссылку, которую они прислали.",
    de: "Wenn Ihre Familie dies für Sie eingerichtet hat, öffnen Sie bitte den persönlichen Link, den sie Ihnen geschickt hat.",
  },
  unknown_cta: {
    en: "I want to set this up for my parent",
    ru: "Я хочу настроить это для родителя",
    de: "Ich möchte das für meine Eltern einrichten",
  },
  loading: { en: "Loading…", ru: "Загрузка…", de: "Lädt…" },
  error: {
    en: "Something went wrong. Please reopen the app.",
    ru: "Что-то пошло не так. Откройте приложение заново.",
    de: "Etwas ist schiefgelaufen. Bitte öffnen Sie die App erneut.",
  },
  back: { en: "Back", ru: "Назад", de: "Zurück" },
  // event types
  ev_resolved: {
    en: "Problem solved",
    ru: "Проблема решена",
    de: "Problem gelöst",
  },
  ev_escalation: {
    en: "Asked for your help",
    ru: "Понадобилась ваша помощь",
    de: "Ihre Hilfe wurde gebraucht",
  },
  ev_safety_stop: {
    en: "⚠️ Safety stop (possible scam)",
    ru: "⚠️ Остановка безопасности (возможно, мошенники)",
    de: "⚠️ Sicherheitsstopp (möglicher Betrug)",
  },
  ev_scam_flag: {
    en: "⚠️ Checked a suspicious message",
    ru: "⚠️ Проверка подозрительного сообщения",
    de: "⚠️ Verdächtige Nachricht geprüft",
  },
  ev_settings_changed: {
    en: "Settings changed",
    ru: "Настройки изменены",
    de: "Einstellungen geändert",
  },
  // scenarios
  sc_wifi: { en: "Internet", ru: "Интернет", de: "Internet" },
  sc_password: { en: "Password", ru: "Пароль", de: "Passwort" },
  sc_os_update: {
    en: "Phone update",
    ru: "Обновление телефона",
    de: "Handy-Update",
  },
  sc_setup: {
    en: "Make it easier",
    ru: "Настройка удобства",
    de: "Einfacher machen",
  },
  sc_scam: {
    en: "Suspicious message",
    ru: "Подозрительное сообщение",
    de: "Verdächtige Nachricht",
  },
  sc_unknown: { en: "Other", ru: "Другое", de: "Sonstiges" },
  st_active: { en: "in progress", ru: "в процессе", de: "läuft" },
  st_resolved: { en: "solved", ru: "решено", de: "gelöst" },
  st_escalated: {
    en: "needed family",
    ru: "нужна семья",
    de: "Familie gebraucht",
  },
  st_closed: { en: "closed", ru: "закрыто", de: "geschlossen" },
};

export function normLang(raw: string | undefined): Lang {
  return raw === "ru" || raw === "de" ? raw : "en";
}

export function t(key: string, lang: Lang): string {
  return STR[key]?.[lang] ?? STR[key]?.en ?? key;
}
