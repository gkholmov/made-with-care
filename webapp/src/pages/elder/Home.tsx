import { useEffect, useState } from "react";
import { api, ElderHome as HomeData } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { tg } from "../../lib/telegram";

/** The elder's visual home: huge, stable, no motion. Topic taps go back to the
 * chat via sendData (the app closes and the playbook continues there). */
export default function ElderHome({ lang: fallbackLang }: { lang: Lang }) {
  const [home, setHome] = useState<HomeData | null>(null);

  useEffect(() => {
    api
      .get<HomeData>("/api/elder/home")
      .then(setHome)
      .catch(() => {});
  }, []);

  if (!home) {
    return (
      <div className="elder flex min-h-screen items-center justify-center text-elder-lg text-tg-hint">
        {t("loading", fallbackLang)}
      </div>
    );
  }
  const lang = (home.language as Lang) || fallbackLang;

  // Drive the playbook over HTTP (works no matter how the app was launched), then
  // close so the elder lands back in the chat where the step appears.
  const sendTopic = async (key: string) => {
    try {
      await api.post("/api/elder/topic", { name: key });
    } catch {
      /* ignore — the chat will still show whatever did happen */
    }
    tg().close();
  };
  const sendPhoto = async () => {
    try {
      await api.post("/api/elder/photo", {});
    } catch {
      /* ignore */
    }
    tg().close();
  };
  const callRelative = () => {
    if (home.relative.telegram_id)
      tg().openTelegramLink(`tg://user?id=${home.relative.telegram_id}`);
  };

  return (
    <div className="elder mx-auto flex min-h-screen max-w-md flex-col gap-4 p-4">
      <h1 className="pt-2 text-center text-elder-xl font-bold">
        {t("hello", lang)}
        {home.name ? `, ${home.name}` : ""}!
      </h1>
      <p className="text-center text-elder-base text-tg-hint">
        {t("what_help", lang)}
      </p>

      <div className="flex flex-col gap-3">
        {home.topics.map((topic) => (
          <button
            key={topic.key}
            onClick={() => sendTopic(topic.key)}
            className="min-h-touch w-full rounded-2xl bg-tg-secondary-bg px-5 text-left text-elder-lg font-semibold active:opacity-70"
          >
            {topic.label}
          </button>
        ))}
      </div>

      <div className="mt-auto flex flex-col gap-3 pb-4">
        <button
          onClick={sendPhoto}
          className="min-h-touch w-full rounded-2xl bg-tg-button px-5 text-elder-lg font-bold text-tg-button-text active:opacity-70"
        >
          📷 {t("show_screen", lang)}
        </button>
        {home.relative.telegram_id && (
          <button
            onClick={callRelative}
            className="min-h-touch w-full rounded-2xl border-4 border-tg-button px-5 text-elder-lg font-bold text-tg-button active:opacity-70"
          >
            📞 {t("call", lang)} {home.relative.name}
          </button>
        )}
      </div>
    </div>
  );
}
