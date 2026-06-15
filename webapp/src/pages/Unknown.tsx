import { Lang, t } from "../lib/i18n";
import { ActionButton } from "../components/ui";

export default function Unknown({
  lang,
  onSetup,
}: {
  lang: Lang;
  onSetup: () => void;
}) {
  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-5 bg-tg-bg p-6 text-center">
      <span className="flex h-20 w-20 items-center justify-center rounded-full border-2 border-tg-button text-tg-button">
        <svg viewBox="0 0 24 24" className="h-10 w-10" aria-hidden="true">
          <path
            d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1 7.8 7.8 7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <h1 className="font-serif text-elder-xl font-bold tracking-tight">
        {t("unknown_title", lang)}
      </h1>
      <p className="text-elder-base text-tg-hint">{t("unknown_body", lang)}</p>
      <ActionButton
        variant="primary"
        size="md"
        label={t("unknown_cta", lang)}
        onClick={onSetup}
      />
    </div>
  );
}
