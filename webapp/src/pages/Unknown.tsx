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
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-5 p-6 text-center">
      <div className="text-5xl">🌼</div>
      <h1 className="text-elder-xl font-bold">{t("unknown_title", lang)}</h1>
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
