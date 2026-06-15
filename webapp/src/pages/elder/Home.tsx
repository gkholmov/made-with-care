/**
 * Home — "Calm & Editorial" direction (designed in Claude, merged here).
 * Presentational launcher: a calm greeting, one dominant "Talk to me", a single
 * "Show my screen", a labeled list of common problems, and a persistent
 * "Call my family" affordance. ElderShell owns all data + actions.
 *
 * Colors are the FIXED editorial palette (sand + blue) — intentionally NOT the
 * device/Telegram theme, so a dark phone theme can't turn the warm UI black.
 * All copy comes through t() (en/ru/de).
 */
import React from "react";
import { ElderHome } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";

/** Topic labels come from the backend with a leading emoji; the screen shows its
 * own inline-SVG icon, so strip the emoji to avoid a doubled icon. */
const stripEmoji = (s: string) =>
  s.replace(/[\p{Extended_Pictographic}️‍]/gu, "").trim();

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
const MicIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <rect x="9" y="2" width="6" height="11" rx="3" {...S} />
    <path d="M5 11a7 7 0 0 0 14 0" {...S} />
    <line x1="12" y1="18" x2="12" y2="22" {...S} />
    <line x1="8" y1="22" x2="16" y2="22" {...S} />
  </Svg>
);
const ScreenIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <rect x="3" y="4" width="18" height="13" rx="2" {...S} />
    <path d="M9 11l3-3 3 3" {...S} />
    <line x1="12" y1="8" x2="12" y2="14" {...S} />
    <line x1="8" y1="21" x2="16" y2="21" {...S} />
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
const PlayIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M7 5l12 7-12 7z" fill="currentColor" />
  </Svg>
);
const ChevronRight = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M9 18l6-6-6-6" {...S} />
  </Svg>
);
const WifiIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M2 8.5a16 16 0 0 1 20 0" {...S} />
    <path d="M5 12a11 11 0 0 1 14 0" {...S} />
    <path d="M8.5 15.5a6 6 0 0 1 7 0" {...S} />
    <line x1="12" y1="19" x2="12" y2="19" {...S} />
  </Svg>
);
const LockIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <rect x="3" y="11" width="18" height="10" rx="2" {...S} />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" {...S} />
  </Svg>
);
const RefreshIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M3 12a9 9 0 0 1 15-6.7L21 8" {...S} />
    <path d="M21 3v5h-5" {...S} />
    <path d="M21 12a9 9 0 0 1-15 6.7L3 16" {...S} />
    <path d="M3 21v-5h5" {...S} />
  </Svg>
);
const SlidersIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <line x1="4" y1="21" x2="4" y2="14" {...S} />
    <line x1="4" y1="10" x2="4" y2="3" {...S} />
    <line x1="12" y1="21" x2="12" y2="12" {...S} />
    <line x1="12" y1="8" x2="12" y2="3" {...S} />
    <line x1="20" y1="21" x2="20" y2="16" {...S} />
    <line x1="20" y1="12" x2="20" y2="3" {...S} />
    <line x1="1" y1="14" x2="7" y2="14" {...S} />
    <line x1="9" y1="8" x2="15" y2="8" {...S} />
    <line x1="17" y1="16" x2="23" y2="16" {...S} />
  </Svg>
);
const ShieldIcon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" {...S} />
  </Svg>
);
const HelpDot = ({ className }: IconProps) => (
  <Svg className={className}>
    <circle cx="12" cy="12" r="9" {...S} />
  </Svg>
);

/** Icon per backend topic key (ph/core/i18n.py). Unknown keys get a neutral dot. */
function TopicIcon({
  topicKey,
  className,
}: {
  topicKey: string;
  className?: string;
}) {
  switch (topicKey) {
    case "wifi":
      return <WifiIcon className={className} />;
    case "password":
      return <LockIcon className={className} />;
    case "os_update":
      return <RefreshIcon className={className} />;
    case "setup":
      return <SlidersIcon className={className} />;
    case "scam":
      return <ShieldIcon className={className} />;
    default:
      return <HelpDot className={className} />;
  }
}

/* ---- component ------------------------------------------------------------- */
export default function Home({
  lang,
  home,
  ongoing,
  recording,
  onResume,
  onTopic,
  onMic,
  onPhoto,
  onCall,
}: {
  lang: Lang;
  home: ElderHome;
  ongoing: boolean;
  recording: boolean;
  onResume: () => void;
  onTopic: (key: string) => void;
  onMic: () => void;
  onPhoto: (file: File) => void;
  onCall: () => void;
}) {
  return (
    <div className="elder min-h-screen w-full bg-[#FBF7EF] px-6 pb-8 pt-4 text-[#2A2620]">
      {/* greeting */}
      <h1 className="mt-2 font-serif text-[30px] font-bold leading-tight tracking-tight">
        {t("hello", lang)}
        {home.name ? `, ${home.name}` : ""}
      </h1>
      <p className="mt-2 text-[18px] leading-snug text-[#7A7163]">
        {t("how_help", lang)}
      </p>

      {/* continue (only when a conversation is in progress) */}
      {ongoing ? (
        <button
          type="button"
          onClick={onResume}
          className="mt-5 flex w-full items-center gap-4 border-y border-[#E7DFCF] py-4 text-left active:opacity-90"
        >
          <span className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-[#2C5D87] text-[#ffffff]">
            <PlayIcon className="h-5 w-5" />
          </span>
          <span className="flex-1">
            <span className="block text-[13px] font-bold uppercase tracking-wide text-[#2C5D87]">
              {t("continue_label", lang)}
            </span>
            <span className="block text-[19px] font-semibold">
              {t("continue_chat", lang)}
            </span>
          </span>
          <ChevronRight className="h-6 w-6 flex-none text-[#A99F8D]" />
        </button>
      ) : null}

      {/* primary: talk to me */}
      <button
        type="button"
        onClick={onMic}
        className={
          "mt-5 flex min-h-[92px] w-full items-center gap-4 rounded-2xl px-6 text-left active:opacity-90 " +
          (recording
            ? "bg-[#B23A2E] text-white"
            : "bg-[#2C5D87] text-[#ffffff]")
        }
      >
        <MicIcon className="h-9 w-9 flex-none" />
        <span className="text-[24px] font-bold">
          {recording ? t("recording", lang) : t("talk_to_me", lang)}
        </span>
      </button>

      {/* secondary: show my screen (file picker → take photo OR pick from gallery) */}
      <label className="mt-3 flex min-h-[84px] w-full cursor-pointer items-center gap-4 rounded-2xl border-[1.5px] border-[#2C5D87] bg-transparent px-6 text-left text-[#2C5D87] active:opacity-90">
        <ScreenIcon className="h-8 w-8 flex-none" />
        <span className="text-[22px] font-bold">{t("show_screen", lang)}</span>
        <input
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onPhoto(f);
            e.target.value = "";
          }}
        />
      </label>

      {/* topics */}
      <h2 className="mb-1 mt-7 font-serif text-[20px] font-bold">
        {t("problems_heading", lang)}
      </h2>
      <ul className="flex flex-col">
        {home.topics.map((topic) => (
          <li key={topic.key}>
            <button
              type="button"
              onClick={() => onTopic(topic.key)}
              className="flex min-h-[74px] w-full items-center gap-4 border-b border-[#E7DFCF] py-3.5 text-left active:opacity-90"
            >
              <span className="flex h-[46px] w-[46px] flex-none items-center justify-center rounded-full bg-[#F2ECDF] text-[#2C5D87]">
                <TopicIcon topicKey={topic.key} className="h-6 w-6" />
              </span>
              <span className="flex-1 text-[21px] font-semibold">
                {stripEmoji(topic.label)}
              </span>
              <ChevronRight className="h-6 w-6 flex-none text-[#A99F8D]" />
            </button>
          </li>
        ))}
      </ul>

      {/* persistent call-family affordance */}
      {home.relative.telegram_id ? (
        <button
          type="button"
          onClick={onCall}
          className="mt-6 flex w-full items-center justify-center gap-3 border-t border-[#E7DFCF] py-4 text-[#2C5D87] active:opacity-90"
        >
          <PhoneIcon className="h-6 w-6" />
          <span className="text-[19px] font-bold">
            {t("call", lang)}
            {home.relative.name ? ` ${home.relative.name}` : ""}
          </span>
        </button>
      ) : null}
    </div>
  );
}
