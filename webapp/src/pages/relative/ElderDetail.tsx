import { useEffect, useState } from "react";
import { api, ElderDetailData, EventItem, SessionSummary } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { tg } from "../../lib/telegram";
import {
  AlertBanner,
  EventFeed,
  SessionList,
} from "../../components/ActivityFeed";

export default function ElderDetail({
  lang,
  elderId,
  onSettings,
}: {
  lang: Lang;
  elderId: number;
  onSettings: () => void;
}) {
  const [detail, setDetail] = useState<ElderDetailData | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  useEffect(() => {
    api
      .get<ElderDetailData>(`/api/relative/elders/${elderId}`)
      .then(setDetail)
      .catch(() => {});
    api
      .get<EventItem[]>(`/api/relative/elders/${elderId}/events?limit=20`)
      .then(setEvents)
      .catch(() => {});
    api
      .get<SessionSummary[]>(
        `/api/relative/elders/${elderId}/sessions?limit=10`,
      )
      .then(setSessions)
      .catch(() => {});
  }, [elderId]);

  if (!detail) {
    return <div className="p-6 text-tg-hint">{t("loading", lang)}</div>;
  }

  const shareJoinLink = () => {
    if (detail.join_link)
      tg().openTelegramLink(
        `https://t.me/share/url?url=${encodeURIComponent(detail.join_link)}`,
      );
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col gap-4 p-4">
      <div className="flex items-center justify-between pt-2">
        <h1 className="text-2xl font-bold">{detail.name}</h1>
        <button
          onClick={onSettings}
          className="rounded-xl bg-tg-secondary-bg px-4 py-2 font-medium active:opacity-70"
        >
          ⚙️ {t("settings", lang)}
        </button>
      </div>

      {!detail.claimed && detail.join_link && (
        <div className="rounded-2xl bg-tg-secondary-bg p-4">
          <p className="mb-3 text-sm">{t("join_link_hint", lang)}</p>
          <button
            onClick={shareJoinLink}
            className="min-h-12 w-full rounded-xl bg-tg-button font-semibold text-tg-button-text active:opacity-70"
          >
            {t("share_link", lang)}
          </button>
        </div>
      )}

      <AlertBanner events={events} lang={lang} />

      <h2 className="text-sm font-medium uppercase tracking-wide text-tg-hint">
        {t("recent_activity", lang)}
      </h2>
      <EventFeed events={events} lang={lang} />

      <h2 className="text-sm font-medium uppercase tracking-wide text-tg-hint">
        {t("sessions", lang)}
      </h2>
      <SessionList sessions={sessions} lang={lang} />
    </div>
  );
}
