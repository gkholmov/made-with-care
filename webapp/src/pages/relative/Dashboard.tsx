import { useEffect, useState } from "react";
import { api, ElderSummary } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";

export default function Dashboard({
  lang,
  onOpen,
  onAdd,
}: {
  lang: Lang;
  onOpen: (id: number) => void;
  onAdd: () => void;
}) {
  const [elders, setElders] = useState<ElderSummary[] | null>(null);

  useEffect(() => {
    api
      .get<ElderSummary[]>("/api/relative/elders")
      .then(setElders)
      .catch(() => setElders([]));
  }, []);

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col gap-4 p-4">
      <h1 className="pt-2 text-2xl font-bold">{t("dashboard", lang)}</h1>
      <h2 className="text-sm font-medium uppercase tracking-wide text-tg-hint">
        {t("your_elders", lang)}
      </h2>

      {elders === null && <p className="text-tg-hint">{t("loading", lang)}</p>}

      <div className="flex flex-col gap-3">
        {elders?.map((e) => (
          <button
            key={e.elder_id}
            onClick={() => onOpen(e.elder_id)}
            className="flex items-center justify-between rounded-2xl bg-tg-secondary-bg p-4 text-left active:opacity-70"
          >
            <div>
              <div className="text-lg font-semibold">{e.name}</div>
              <div className="text-sm text-tg-hint">
                {e.claimed
                  ? e.last_event_at
                    ? new Date(e.last_event_at).toLocaleString()
                    : t("no_activity", lang)
                  : t("not_claimed", lang)}
              </div>
            </div>
            {e.open_alerts > 0 && (
              <span className="rounded-full bg-red-500 px-3 py-1 text-sm font-bold text-white">
                {e.open_alerts} {t("alerts", lang)}
              </span>
            )}
          </button>
        ))}
      </div>

      <button
        onClick={onAdd}
        className="mt-2 min-h-14 rounded-2xl bg-tg-button px-5 font-semibold text-tg-button-text active:opacity-70"
      >
        ＋ {t("add_elder", lang)}
      </button>
    </div>
  );
}
