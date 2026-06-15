import { EventItem, SessionSummary } from "../lib/api";
import { Lang, t } from "../lib/i18n";

export function AlertBanner({
  events,
  lang,
}: {
  events: EventItem[];
  lang: Lang;
}) {
  const alert = events.find(
    (e) => e.type === "safety_stop" || e.type === "scam_flag",
  );
  if (!alert) return null;
  return (
    <div className="rounded-2xl border-2 border-danger bg-danger/5 p-4 text-danger">
      <div className="font-serif text-elder-base font-bold">
        {t(`ev_${alert.type}`, lang)}
      </div>
      <div className="text-tg-hint">{new Date(alert.at).toLocaleString()}</div>
      {alert.meta && <div className="mt-1">{alert.meta}</div>}
    </div>
  );
}

export function EventFeed({
  events,
  lang,
}: {
  events: EventItem[];
  lang: Lang;
}) {
  if (!events.length)
    return <p className="text-tg-hint">{t("no_activity", lang)}</p>;
  return (
    <ul className="flex flex-col gap-2">
      {events.map((e, i) => (
        <li
          key={i}
          className="rounded-xl border border-line bg-tg-secondary-bg p-3"
        >
          <div
            className={
              "text-elder-base font-semibold " +
              (e.type.includes("scam") || e.type === "safety_stop"
                ? "text-danger"
                : "")
            }
          >
            {t(`ev_${e.type}`, lang)}
          </div>
          <div className="text-tg-hint">{new Date(e.at).toLocaleString()}</div>
        </li>
      ))}
    </ul>
  );
}

export function SessionList({
  sessions,
  lang,
}: {
  sessions: SessionSummary[];
  lang: Lang;
}) {
  if (!sessions.length)
    return <p className="text-tg-hint">{t("no_activity", lang)}</p>;
  return (
    <ul className="flex flex-col gap-2">
      {sessions.map((s, i) => (
        <li
          key={i}
          className="flex items-center justify-between rounded-xl border border-line bg-tg-secondary-bg p-3"
        >
          <span className="text-elder-base font-semibold">
            {t(`sc_${s.scenario}`, lang)}
          </span>
          <span className="text-tg-hint">{t(`st_${s.state}`, lang)}</span>
        </li>
      ))}
    </ul>
  );
}
