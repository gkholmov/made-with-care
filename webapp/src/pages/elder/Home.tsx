import { ElderHome } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";

/** A full-width photo tile. `capture` forces the camera; without it the OS shows the
 * gallery / file chooser so the elder can upload any existing image. */
function PhotoTile({
  label,
  capture,
  onPhoto,
}: {
  label: string;
  capture?: boolean;
  onPhoto: (file: File) => void;
}) {
  return (
    <label className="flex min-h-touch w-full cursor-pointer items-center justify-center rounded-2xl bg-tg-secondary-bg px-5 text-elder-lg font-semibold active:opacity-70">
      {label}
      <input
        type="file"
        accept="image/*"
        {...(capture ? { capture: "environment" as const } : {})}
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onPhoto(f);
          e.target.value = "";
        }}
      />
    </label>
  );
}

/** Presentational launcher: voice, key problems, screen, call. ElderShell owns all
 * the actions and the conversation state. Huge, stable, no motion. */
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
    <div className="elder mx-auto flex min-h-screen max-w-md flex-col gap-4 p-4">
      <h1 className="pt-2 text-center text-elder-xl font-bold">
        {t("hello", lang)}
        {home.name ? `, ${home.name}` : ""}!
      </h1>
      <p className="text-center text-elder-base text-tg-hint">
        {t("what_help", lang)}
      </p>

      {ongoing && (
        <button
          onClick={onResume}
          className="min-h-touch w-full rounded-2xl border-4 border-tg-button bg-tg-bg px-5 text-elder-lg font-bold text-tg-button active:opacity-70"
        >
          {t("continue_chat", lang)}
        </button>
      )}

      {/* Voice first — the primary way to ask for help. */}
      <button
        onClick={onMic}
        className={
          "min-h-touch w-full rounded-2xl px-5 text-elder-lg font-bold active:opacity-70 " +
          (recording
            ? "bg-red-500 text-white"
            : "bg-tg-button text-tg-button-text")
        }
      >
        {recording ? t("recording", lang) : t("tell_problem", lang)}
      </button>

      <div className="flex flex-col gap-3">
        {home.topics.map((topic) => (
          <button
            key={topic.key}
            onClick={() => onTopic(topic.key)}
            className="min-h-touch w-full rounded-2xl bg-tg-secondary-bg px-5 text-left text-elder-lg font-semibold active:opacity-70"
          >
            {topic.label}
          </button>
        ))}
      </div>

      <div className="mt-auto flex flex-col gap-3 pb-4">
        <PhotoTile label={t("photo_hint", lang)} capture onPhoto={onPhoto} />
        <PhotoTile label={t("gallery", lang)} onPhoto={onPhoto} />
        {home.relative.telegram_id && (
          <button
            onClick={onCall}
            className="min-h-touch w-full rounded-2xl border-4 border-tg-button px-5 text-elder-lg font-bold text-tg-button active:opacity-70"
          >
            📞 {t("call", lang)} {home.relative.name}
          </button>
        )}
      </div>
    </div>
  );
}
