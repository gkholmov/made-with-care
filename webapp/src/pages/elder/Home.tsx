import { ElderHome } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { ActionButton, PhotoPicker, SectionLabel } from "../../components/ui";

/** Talk-first launcher: one dominant "talk" action, a single "show my screen", a
 * clearly-labeled list of common problems, and a persistent "Call my family" footer.
 * Presentational — ElderShell owns all the actions and conversation state. */
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
  const firstRun = !localStorage.getItem("ph_seen_home");
  if (firstRun) localStorage.setItem("ph_seen_home", "1");

  return (
    <div className="elder mx-auto flex min-h-screen max-w-md flex-col gap-4 p-4">
      <h1 className="pt-2 text-center text-elder-xl font-bold">
        {t("hello", lang)}
        {home.name ? `, ${home.name}` : ""}
      </h1>
      <p className="text-center text-elder-base text-tg-hint">
        {t("how_help", lang)}
      </p>

      {firstRun && !ongoing && (
        <p className="rounded-2xl bg-tg-secondary-bg p-4 text-center text-elder-base text-tg-hint">
          {t("first_run_hint", lang)}
        </p>
      )}

      {ongoing && (
        <ActionButton
          variant="ghost"
          size="lg"
          label={t("continue_chat", lang)}
          onClick={onResume}
        />
      )}

      {/* Primary: talk to me. */}
      <ActionButton
        variant={recording ? "danger" : "primary"}
        size="lg"
        label={recording ? t("recording", lang) : t("tell_problem", lang)}
        onClick={onMic}
      />

      {/* One photo control — the OS lets them take a photo OR pick from the gallery. */}
      <PhotoPicker
        variant="secondary"
        size="lg"
        label={t("show_my_screen", lang)}
        onFile={onPhoto}
      />

      <SectionLabel>{t("pick_problem", lang)}</SectionLabel>
      <div className="flex flex-col gap-3">
        {home.topics.map((topic) => (
          <ActionButton
            key={topic.key}
            variant="secondary"
            size="md"
            align="start"
            label={topic.label}
            onClick={() => onTopic(topic.key)}
          />
        ))}
      </div>

      {/* Persistent footer — always last, always in the same place. */}
      {home.relative.telegram_id && (
        <div className="mt-auto pt-2">
          <ActionButton
            variant="ghost"
            size="lg"
            label={t("call_family", lang)}
            onClick={onCall}
          />
        </div>
      )}
    </div>
  );
}
