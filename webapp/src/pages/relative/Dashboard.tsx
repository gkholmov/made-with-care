import { useEffect, useState } from "react";
import { api, ElderSummary } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { ActionButton, Card, SectionLabel } from "../../components/ui";

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
      <h1 className="pt-2 text-elder-xl font-bold">{t("dashboard", lang)}</h1>
      <SectionLabel>{t("your_elders", lang)}</SectionLabel>

      {elders === null && <p className="text-tg-hint">{t("loading", lang)}</p>}

      <div className="flex flex-col gap-3">
        {elders?.map((e) => (
          <Card key={e.elder_id} onClick={() => onOpen(e.elder_id)}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-elder-base font-semibold">{e.name}</div>
                <div className="text-tg-hint">
                  {e.claimed
                    ? e.last_event_at
                      ? new Date(e.last_event_at).toLocaleString()
                      : t("no_activity", lang)
                    : t("not_claimed", lang)}
                </div>
              </div>
              {e.open_alerts > 0 && (
                <span className="rounded-full bg-danger px-3 py-1 font-bold text-danger-text">
                  {e.open_alerts} {t("alerts", lang)}
                </span>
              )}
            </div>
          </Card>
        ))}
      </div>

      <div className="mt-2">
        <ActionButton
          variant="primary"
          size="md"
          label={`＋ ${t("add_elder", lang)}`}
          onClick={onAdd}
        />
      </div>
    </div>
  );
}
