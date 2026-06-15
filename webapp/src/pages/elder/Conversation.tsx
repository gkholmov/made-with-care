/**
 * Conversation — "Calm & Editorial" direction (designed in Claude, merged here).
 * In-app chat: a persistent header (always one tap back to Home), big calm
 * bubbles, and a predictable input — an always-visible text box, a "Did it
 * work?" prompt that appears once the helper has given a step, and Talk/Show as
 * other ways to answer. ElderShell owns all data + actions; this is the view.
 *
 * Colors are the FIXED editorial palette (sand + blue) — intentionally NOT the
 * device/Telegram theme, so a dark phone theme can't turn the warm UI black.
 * All copy comes through t() (en/ru/de). The draft string is the only local
 * state — everything else is prop-driven.
 */
import React, { useEffect, useRef, useState } from "react";
import { Reply } from "../../lib/api";
import { Lang, t, affirmKey } from "../../lib/i18n";

export type Msg = { role: "bot" | "me"; text: string; image?: string };

const TERMINAL = ["resolved", "escalated", "safety_stop"];

/* ---- inline icons (monochrome, currentColor) ------------------------------- */
const S = {
  fill: "none" as const,
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};
type IconProps = { className?: string };
const Svg = ({
  className,
  children,
}: IconProps & { children: React.ReactNode }) => (
  <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
    {children}
  </svg>
);
const BackIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M15 18l-6-6 6-6" {...S} />
  </Svg>
);
const PhoneIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path
      d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.8 2z"
      {...S}
    />
  </Svg>
);
const CheckIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M20 6L9 17l-5-5" {...S} />
  </Svg>
);
const XIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <line x1="18" y1="6" x2="6" y2="18" {...S} />
    <line x1="6" y1="6" x2="18" y2="18" {...S} />
  </Svg>
);
const MicIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <rect x="9" y="2" width="6" height="11" rx="3" {...S} />
    <path d="M5 11a7 7 0 0 0 14 0" {...S} />
    <line x1="12" y1="18" x2="12" y2="22" {...S} />
    <line x1="8" y1="22" x2="16" y2="22" {...S} />
  </Svg>
);
const CameraIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path
      d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h3l2-3h8l2 3h3a2 2 0 0 1 2 2z"
      {...S}
    />
    <circle cx="12" cy="13" r="4" {...S} />
  </Svg>
);
const SendIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <line x1="22" y1="2" x2="11" y2="13" {...S} />
    <path d="M22 2l-7 20-4-9-9-4 20-7z" {...S} />
  </Svg>
);
const HelpIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <circle cx="12" cy="12" r="10" {...S} />
    <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3" {...S} />
    <line x1="12" y1="17" x2="12" y2="17" {...S} />
  </Svg>
);

/* ---- component ------------------------------------------------------------- */
export default function Conversation({
  lang,
  messages,
  reply,
  pending,
  pendingKind,
  topicTitle,
  canCall,
  relativeName,
  recording,
  onSend,
  onConfirm,
  onMic,
  onPhoto,
  onCall,
  onGoHome,
  onFinish,
}: {
  lang: Lang;
  messages: Msg[];
  reply: Reply | null;
  pending: boolean;
  pendingKind: "text" | "voice" | "photo";
  topicTitle: string;
  canCall: boolean;
  relativeName: string;
  recording: boolean;
  onSend: (text: string) => void;
  onConfirm: (yes: boolean) => void;
  onMic: () => void;
  onPhoto: (file: File) => void;
  onCall: () => void;
  onGoHome: () => void;
  onFinish: () => void;
}) {
  const [draft, setDraft] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages, pending]);

  const state = reply?.state ?? "active";
  const terminal = TERMINAL.includes(state);
  const needsFamily = state === "escalated" || state === "safety_stop";
  const statusText = recording
    ? t("transcribing", lang)
    : pendingKind === "photo"
      ? t("status_sending_photo", lang)
      : pendingKind === "voice"
        ? t("transcribing", lang)
        : t("status_thinking", lang);

  const handleSend = () => {
    const text = draft.trim();
    if (!text || pending) return;
    onSend(text);
    setDraft("");
  };

  // The "Did it work?" prompt only makes sense once the helper has walked the
  // elder through a step (after the 2nd helper message) AND the helper actually
  // asked a yes/no check. When the helper asks a choice/open question it sets
  // confirm_kind="ask", and we hide the yes/no buttons so the elder just replies.
  const botCount = messages.filter((m) => m.role === "bot").length;
  const choices = (!terminal && reply?.choices) || [];
  const hasChoices = choices.length > 0;
  const showConfirm =
    botCount >= 2 && reply?.confirm_kind !== "ask" && !hasChoices;

  const callLabel = relativeName
    ? `${t("call", lang)} ${relativeName}`
    : t("call_now", lang);

  return (
    <div className="elder flex h-screen w-full flex-col bg-[#FBF7EF] text-[#2A2620]">
      {/* persistent header: back + topic + quick call */}
      <header className="flex flex-none items-center gap-2.5 border-b border-[#E7DFCF] px-4 pb-3.5 pt-2">
        <button
          type="button"
          onClick={onGoHome}
          aria-label={t("back_home", lang)}
          className="flex h-[52px] w-[52px] flex-none items-center justify-center rounded-full bg-[#F2ECDF] text-[#2C5D87] active:opacity-90"
        >
          <BackIcon className="h-6 w-6" />
        </button>
        <div className="min-w-0 flex-1">
          <div className="text-[13px] font-bold uppercase tracking-wide text-[#7A7163]">
            {t("helping_with", lang)}
          </div>
          <div className="truncate font-serif text-[20px] font-bold">
            {topicTitle}
          </div>
        </div>
        {canCall ? (
          <button
            type="button"
            onClick={onCall}
            aria-label={callLabel}
            className="flex h-[52px] w-[52px] flex-none items-center justify-center rounded-full bg-[#2C5D87] text-[#ffffff] active:opacity-90"
          >
            <PhoneIcon className="h-6 w-6" />
          </button>
        ) : null}
      </header>

      {/* message thread (scrolls) */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col gap-3.5 p-[18px]">
          {messages.map((m, i) =>
            m.role === "bot" ? (
              <div key={i} className="max-w-[88%] self-start">
                <div className="whitespace-pre-wrap rounded-2xl bg-[#F2ECDF] px-4 py-3.5 text-[19px] leading-snug">
                  {m.text}
                </div>
                {m.image ? (
                  <div className="mt-2.5 overflow-hidden rounded-2xl border border-[#E7DFCF] bg-white">
                    <img src={m.image} alt="" className="block w-full" />
                  </div>
                ) : null}
              </div>
            ) : (
              <div key={i} className="max-w-[88%] self-end">
                {m.image ? (
                  <div className="mb-2 overflow-hidden rounded-2xl border border-[#E7DFCF] bg-white">
                    <img src={m.image} alt="" className="block w-full" />
                  </div>
                ) : null}
                <div className="whitespace-pre-wrap rounded-2xl bg-[#2C5D87] px-4 py-3.5 text-[19px] leading-snug text-[#ffffff]">
                  {m.text}
                </div>
              </div>
            ),
          )}

          {/* word-based status while the helper works */}
          {pending ? (
            <div className="flex items-center gap-2.5 self-start rounded-2xl bg-[#F2ECDF] px-4 py-3.5 text-[18px] font-semibold text-[#7A7163]">
              {statusText}
              <span className="flex items-center gap-1.5">
                <span className="block h-[7px] w-[7px] rounded-full bg-[#9DB0A6]" />
                <span className="block h-[7px] w-[7px] rounded-full bg-[#9DB0A6]" />
                <span className="block h-[7px] w-[7px] rounded-full bg-[#9DB0A6]" />
              </span>
            </div>
          ) : null}
          <div ref={bottom} />
        </div>
      </div>

      {/* bottom action area */}
      <div className="flex-none border-t border-[#E7DFCF] px-[18px] pb-[22px] pt-3.5">
        {needsFamily ? (
          /* escalated / safety_stop → prominent Call my family */
          <div className="rounded-2xl border border-[#CBD9E6] bg-[#EDF1F6] p-5 text-center">
            <span className="mb-2.5 inline-flex h-[54px] w-[54px] items-center justify-center rounded-full border-[1.5px] border-[#2C5D87] bg-white text-[#2C5D87]">
              <HelpIcon className="h-7 w-7" />
            </span>
            <div className="font-serif text-[23px] font-bold">
              {t("escalated_title", lang)}
            </div>
            {relativeName ? (
              <div className="mt-1 text-[18px] text-[#7A7163]">
                {t("connect_with", lang)} {relativeName}.
              </div>
            ) : null}
            {canCall ? (
              <button
                type="button"
                onClick={onCall}
                className="mt-4 flex min-h-[88px] w-full items-center justify-center gap-3 rounded-2xl bg-[#2C5D87] text-[23px] font-bold text-[#ffffff] active:opacity-90"
              >
                <PhoneIcon className="h-[30px] w-[30px]" />
                {callLabel}
              </button>
            ) : null}
            <button
              type="button"
              onClick={onFinish}
              className="mt-3 text-[17px] font-bold text-[#7A7163] active:opacity-90"
            >
              {t("back", lang)}
            </button>
          </div>
        ) : terminal ? (
          /* resolved → done / back to topics */
          <div className="px-1 py-1.5 text-center">
            <span className="mb-2 inline-flex h-[54px] w-[54px] items-center justify-center rounded-full bg-[#2C5D87] text-[#ffffff]">
              <CheckIcon className="h-7 w-7" />
            </span>
            <div className="font-serif text-[23px] font-bold">
              {t("resolved_title", lang)}
            </div>
            <button
              type="button"
              onClick={onFinish}
              className="mt-3.5 flex min-h-[80px] w-full items-center justify-center gap-2.5 rounded-2xl bg-[#2C5D87] text-[21px] font-bold text-[#ffffff] active:opacity-90"
            >
              <BackIcon className="h-6 w-6" />
              {t("back_to_topics", lang)}
            </button>
          </div>
        ) : (
          /* active → (confirm after 2nd helper message) + input + other ways */
          <div>
            {showConfirm ? (
              <>
                <div className="mb-2 text-center font-serif text-[18px] font-bold">
                  {t("did_it_work", lang)}
                </div>
                <div className="flex gap-2.5">
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => onConfirm(true)}
                    className="flex min-h-[52px] flex-1 items-center justify-center gap-2 rounded-xl bg-[#2C5D87] text-[#ffffff] active:opacity-90 disabled:opacity-40"
                  >
                    <CheckIcon className="h-5 w-5" />
                    <span className="text-[17px] font-bold">
                      {t(affirmKey(reply?.confirm_kind), lang)}
                    </span>
                  </button>
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => onConfirm(false)}
                    className="flex min-h-[52px] flex-1 items-center justify-center gap-2 rounded-xl border-[1.5px] border-[#C9BFA9] bg-[#FBF7EF] text-[#5C5345] active:opacity-90 disabled:opacity-40"
                  >
                    <XIcon className="h-5 w-5" />
                    <span className="text-[17px] font-bold">
                      {t("not_yet_plain", lang)}
                    </span>
                  </button>
                </div>
              </>
            ) : null}

            {/* the AI offered a choice — big tappable options instead of yes/no */}
            {hasChoices ? (
              <div className="flex flex-col gap-2.5">
                {choices.map((c, i) => (
                  <button
                    key={i}
                    type="button"
                    disabled={pending}
                    onClick={() => onSend(c)}
                    className="flex min-h-[60px] w-full items-center justify-center rounded-2xl border-[1.5px] border-[#2C5D87] bg-[#FBF7EF] px-4 text-[19px] font-bold text-[#2C5D87] active:opacity-90 disabled:opacity-40"
                  >
                    {c}
                  </button>
                ))}
              </div>
            ) : null}

            {/* always-visible text box — no need to tap "Type" first */}
            <div className="mt-3 flex items-stretch gap-2.5">
              <input
                type="text"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSend();
                }}
                placeholder={t("type_here", lang)}
                className="min-h-[56px] flex-1 rounded-xl border-[1.5px] border-[#C9BFA9] bg-[#FBF7EF] px-4 text-[19px] text-[#2A2620] outline-none placeholder:text-[#A99F8D] focus:border-[#2C5D87]"
              />
              <button
                type="button"
                aria-label={t("send", lang)}
                disabled={pending || !draft.trim()}
                onClick={handleSend}
                className="flex min-h-[56px] items-center justify-center rounded-xl bg-[#2C5D87] px-5 text-[#ffffff] active:opacity-90 disabled:opacity-40"
              >
                <SendIcon className="h-6 w-6" />
              </button>
            </div>

            {/* other ways to answer: talk or show */}
            <div className="mb-2.5 mt-3.5 text-center text-[13px] font-bold uppercase tracking-wide text-[#A99F8D]">
              {t("other_ways", lang)}
            </div>
            <div className="flex gap-2.5">
              <button
                type="button"
                onClick={onMic}
                aria-pressed={recording}
                className={
                  "flex min-h-[56px] flex-1 items-center justify-center gap-2 rounded-xl active:opacity-90 " +
                  (recording
                    ? "bg-[#B23A2E] text-white"
                    : "bg-[#F2ECDF] text-[#2C5D87]")
                }
              >
                <MicIcon className="h-5 w-5" />
                <span
                  className={
                    "text-[16px] font-bold " +
                    (recording ? "" : "text-[#5C5345]")
                  }
                >
                  {recording ? t("transcribing", lang) : t("talk_word", lang)}
                </span>
              </button>

              <label className="flex min-h-[56px] flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl bg-[#F2ECDF] text-[#2C5D87] active:opacity-90">
                <CameraIcon className="h-5 w-5" />
                <span className="text-[16px] font-bold text-[#5C5345]">
                  {t("show_word", lang)}
                </span>
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  disabled={pending}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) onPhoto(f);
                    e.target.value = "";
                  }}
                />
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
