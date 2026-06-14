import { useEffect, useState } from "react";
import { api, ElderDetailData } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";

export default function Settings({
  lang,
  elderId,
}: {
  lang: Lang;
  elderId: number;
}) {
  const [detail, setDetail] = useState<ElderDetailData | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .get<ElderDetailData>(`/api/relative/elders/${elderId}`)
      .then(setDetail)
      .catch(() => {});
  }, [elderId]);

  if (!detail)
    return <div className="p-6 text-tg-hint">{t("loading", lang)}</div>;

  const patch = async (body: Record<string, string>) => {
    setBusy(true);
    setSaved(false);
    try {
      await api.patch(`/api/relative/elders/${elderId}`, body);
      setDetail({ ...detail, ...body } as ElderDetailData);
      setSaved(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col gap-5 p-4">
      <h1 className="pt-2 text-elder-xl font-bold">
        ⚙️ {detail.name} — {t("settings", lang)}
      </h1>

      <Section title={t("language", lang)}>
        <Row
          options={[
            ["en", "English"],
            ["ru", "Русский"],
            ["de", "Deutsch"],
          ]}
          value={detail.language}
          busy={busy}
          onPick={(v) => patch({ language: v })}
        />
      </Section>

      <Section title={t("phone", lang)}>
        <Row
          options={[
            ["ios", "iPhone"],
            ["android", "Android"],
          ]}
          value={detail.phone_os}
          busy={busy}
          onPick={(v) => patch({ phone_os: v })}
        />
      </Section>

      <Section title={t("phone_age", lang)}>
        <Row
          options={[
            ["new", t("w_new", lang)],
            ["old", t("w_old", lang)],
          ]}
          value={detail.phone_age}
          busy={busy}
          onPick={(v) => patch({ phone_age: v })}
        />
      </Section>

      {saved && (
        <p className="text-center text-elder-base font-semibold text-success">
          {t("saved", lang)}
        </p>
      )}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm font-medium uppercase tracking-wide text-tg-hint">
        {title}
      </h2>
      {children}
    </div>
  );
}

function Row({
  options,
  value,
  busy,
  onPick,
}: {
  options: [string, string][];
  value: string;
  busy: boolean;
  onPick: (v: string) => void;
}) {
  return (
    <div className="flex gap-2">
      {options.map(([v, label]) => (
        <button
          key={v}
          disabled={busy}
          onClick={() => onPick(v)}
          className={
            "min-h-touch flex-1 rounded-2xl text-elder-base font-semibold active:opacity-70 disabled:opacity-40 " +
            (v === value
              ? "bg-tg-button text-tg-button-text"
              : "bg-tg-secondary-bg")
          }
        >
          {label}
        </button>
      ))}
    </div>
  );
}
