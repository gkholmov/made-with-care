import { Lang, t } from "../lib/i18n";

export default function Unknown({
  lang,
  onSetup,
}: {
  lang: Lang;
  onSetup: () => void;
}) {
  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-5 p-6 text-center">
      <div className="text-5xl">🌼</div>
      <h1 className="text-2xl font-bold">{t("unknown_title", lang)}</h1>
      <p className="text-tg-hint">{t("unknown_body", lang)}</p>
      <button
        onClick={onSetup}
        className="min-h-14 w-full rounded-2xl bg-tg-button px-5 font-semibold text-tg-button-text active:opacity-70"
      >
        {t("unknown_cta", lang)}
      </button>
    </div>
  );
}
