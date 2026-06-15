import { useEffect, useState } from "react";
import { api, ElderDetailData, EventItem, SessionSummary } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { tg } from "../../lib/telegram";
import {
  AlertBanner,
  EventFeed,
  SessionList,
} from "../../components/ActivityFeed";
import { ActionButton, SectionLabel } from "../../components/ui";

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
    <div className="mx-auto flex min-h-screen max-w-md flex-col gap-4 bg-tg-bg p-4">
      <div className="flex items-center justify-between gap-3 pt-2">
        <h1 className="font-serif text-elder-xl font-bold tracking-tight">
          {detail.name}
        </h1>
        <button
          onClick={onSettings}
          className="shrink-0 rounded-xl border border-line bg-tg-secondary-bg px-4 py-3 text-elder-base font-semibold text-tg-button active:opacity-70"
        >
          {t("settings", lang)}
        </button>
      </div>

      {!detail.claimed && detail.join_link && (
        <div className="rounded-2xl bg-tg-secondary-bg p-4">
          <p className="mb-3 text-elder-base">{t("join_link_hint", lang)}</p>
          <ActionButton
            variant="primary"
            size="md"
            label={t("share_link", lang)}
            onClick={shareJoinLink}
          />
        </div>
      )}

      <AlertBanner events={events} lang={lang} />

      <SectionLabel>{t("recent_activity", lang)}</SectionLabel>
      <EventFeed events={events} lang={lang} />

      <SectionLabel>{t("sessions", lang)}</SectionLabel>
      <SessionList sessions={sessions} lang={lang} />
    </div>
  );
}
