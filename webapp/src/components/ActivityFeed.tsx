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
    <div className="rounded-2xl border-2 border-red-500 bg-red-50 p-4 text-red-800">
      <div className="font-bold">{t(`ev_${alert.type}`, lang)}</div>
      <div className="text-sm">{new Date(alert.at).toLocaleString()}</div>
      {alert.meta && <div className="text-sm">{alert.meta}</div>}
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
        <li key={i} className="rounded-xl bg-tg-secondary-bg p-3">
          <div
            className={
              e.type.includes("scam") || e.type === "safety_stop"
                ? "font-semibold text-red-600"
                : "font-semibold"
            }
          >
            {t(`ev_${e.type}`, lang)}
          </div>
          <div className="text-sm text-tg-hint">
            {new Date(e.at).toLocaleString()}
          </div>
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
          className="flex items-center justify-between rounded-xl bg-tg-secondary-bg p-3"
        >
          <span className="font-medium">{t(`sc_${s.scenario}`, lang)}</span>
          <span className="text-sm text-tg-hint">
            {t(`st_${s.state}`, lang)}
          </span>
        </li>
      ))}
    </ul>
  );
}
