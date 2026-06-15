import { useState } from "react";
import { api, SetupResult } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { tg } from "../../lib/telegram";
import { ActionButton } from "../../components/ui";

/** Mirrors the chat /setup conversation as one friendly form. */
export default function SetupWizard({
  lang,
  onDone,
}: {
  lang: Lang;
  onDone: () => void;
}) {
  const [name, setName] = useState("");
  const [elderLang, setElderLang] = useState<Lang>(lang);
  const [os, setOs] = useState<"ios" | "android">("android");
  const [age, setAge] = useState<"new" | "old">("old");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<SetupResult | null>(null);

  const submit = async () => {
    if (!name.trim() || busy) return;
    setBusy(true);
    try {
      const res = await api.post<SetupResult>("/api/relative/setup", {
        name: name.trim(),
        language: elderLang,
        phone_os: os,
        phone_age: age,
        email: email.trim(),
        relative_name: tg().initDataUnsafe.user?.first_name ?? "",
      });
      setResult(res);
    } finally {
      setBusy(false);
    }
  };

  if (result) {
    const share = () => {
      if (result.link)
        tg().openTelegramLink(
          `https://t.me/share/url?url=${encodeURIComponent(result.link)}`,
        );
    };
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col gap-4 bg-tg-bg p-4">
        <h1 className="pt-2 font-serif text-elder-xl font-bold tracking-tight">
          {t("wizard_title", lang)}
        </h1>
        <p className="text-elder-base">{t("join_link_hint", lang)}</p>
        {result.link && (
          <code className="break-all rounded-xl border border-line bg-tg-secondary-bg p-3 text-elder-base">
            {result.link}
          </code>
        )}
        <ActionButton
          variant="primary"
          size="md"
          label={t("share_link", lang)}
          onClick={share}
        />
        <ActionButton
          variant="secondary"
          size="md"
          label={t("back", lang)}
          onClick={onDone}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col gap-4 bg-tg-bg p-4">
      <h1 className="pt-2 font-serif text-elder-xl font-bold tracking-tight">
        {t("wizard_title", lang)}
      </h1>

      <Label text={t("w_name", lang)}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={120}
          className="w-full rounded-2xl border border-line bg-tg-secondary-bg p-4 text-elder-base outline-none focus:border-tg-button"
        />
      </Label>

      <Label text={t("w_lang", lang)}>
        <Choice
          options={[
            ["en", "English"],
            ["ru", "Русский"],
            ["de", "Deutsch"],
          ]}
          value={elderLang}
          onPick={(v) => setElderLang(v as Lang)}
        />
      </Label>

      <Label text={t("w_os", lang)}>
        <Choice
          options={[
            ["ios", "iPhone"],
            ["android", "Android"],
          ]}
          value={os}
          onPick={(v) => setOs(v as "ios" | "android")}
        />
      </Label>

      <Label text={t("w_age", lang)}>
        <Choice
          options={[
            ["new", t("w_new", lang)],
            ["old", t("w_old", lang)],
          ]}
          value={age}
          onPick={(v) => setAge(v as "new" | "old")}
        />
      </Label>

      <Label text={t("w_email", lang)}>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          type="email"
          maxLength={200}
          className="w-full rounded-2xl border border-line bg-tg-secondary-bg p-4 text-elder-base outline-none focus:border-tg-button"
        />
      </Label>

      <div className="mt-2">
        <ActionButton
          variant="primary"
          size="md"
          label={busy ? "…" : t("create_link", lang)}
          disabled={!name.trim() || busy}
          onClick={submit}
        />
      </div>
    </div>
  );
}

function Label({
  text,
  children,
}: {
  text: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-2">
      <span className="text-elder-base font-semibold text-tg-hint">{text}</span>
      {children}
    </label>
  );
}

function Choice({
  options,
  value,
  onPick,
}: {
  options: [string, string][];
  value: string;
  onPick: (v: string) => void;
}) {
  return (
    <div className="flex gap-2">
      {options.map(([v, label]) => (
        <button
          key={v}
          type="button"
          onClick={() => onPick(v)}
          className={
            "min-h-touch flex-1 rounded-2xl text-elder-base font-semibold active:opacity-70 " +
            (v === value
              ? "bg-tg-button text-tg-button-text"
              : "border border-line bg-tg-secondary-bg text-tg-text")
          }
        >
          {label}
        </button>
      ))}
    </div>
  );
}
