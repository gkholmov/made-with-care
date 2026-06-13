import { useEffect, useRef, useState } from "react";
import { Reply } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";

export type Msg = { role: "bot" | "me"; text: string; image?: string };

const TERMINAL = ["resolved", "escalated", "safety_stop"];

/** In-app conversation: a persistent header (always a tap back to Home), chat
 * bubbles, and an input bar that adapts to the latest reply. */
export default function Conversation({
  lang,
  messages,
  reply,
  pending,
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

  const submit = () => {
    const text = draft.trim();
    if (!text || pending) return;
    setDraft("");
    onSend(text);
  };

  const state = reply?.state ?? "active";
  const terminal = TERMINAL.includes(state);

  return (
    <div className="elder flex h-screen flex-col">
      {/* header — always a way back to the launcher */}
      <div className="flex items-center gap-2 border-b border-tg-secondary-bg px-3 py-3">
        <button
          onClick={onGoHome}
          className="min-h-12 rounded-xl bg-tg-secondary-bg px-4 text-elder-base font-semibold active:opacity-70"
        >
          ‹ {t("back_home", lang)}
        </button>
      </div>

      {/* message list */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <div className="mx-auto flex max-w-md flex-col gap-3">
          {messages.map((m, i) => (
            <Bubble key={i} role={m.role} text={m.text} image={m.image} />
          ))}
          {pending && (
            <Bubble
              role="bot"
              text={recording ? t("transcribing", lang) : t("typing", lang)}
              muted
            />
          )}
          <div ref={bottom} />
        </div>
      </div>

      {/* input bar */}
      <div className="border-t border-tg-secondary-bg bg-tg-bg px-3 py-3">
        <div className="mx-auto flex max-w-md flex-col gap-3">
          {terminal ? (
            <>
              {(state === "escalated" || state === "safety_stop") &&
                canCall && (
                  <button
                    onClick={onCall}
                    className="min-h-touch w-full rounded-2xl bg-tg-button px-5 text-elder-lg font-bold text-tg-button-text active:opacity-70"
                  >
                    📞 {t("call", lang)} {relativeName}
                  </button>
                )}
              <button
                onClick={onFinish}
                className="min-h-touch w-full rounded-2xl bg-tg-secondary-bg px-5 text-elder-lg font-semibold active:opacity-70"
              >
                {t("back_home", lang)}
              </button>
            </>
          ) : (
            <>
              {reply?.expect_confirm && (
                <div className="flex gap-3">
                  <button
                    disabled={pending}
                    onClick={() => onConfirm(true)}
                    className="min-h-touch flex-1 rounded-2xl bg-tg-button px-3 text-elder-lg font-bold text-tg-button-text active:opacity-70 disabled:opacity-40"
                  >
                    {t("conf_worked", lang)}
                  </button>
                  <button
                    disabled={pending}
                    onClick={() => onConfirm(false)}
                    className="min-h-touch flex-1 rounded-2xl border-4 border-tg-button px-3 text-elder-lg font-bold text-tg-button active:opacity-70 disabled:opacity-40"
                  >
                    {t("conf_not_yet", lang)}
                  </button>
                </div>
              )}
              {/* voice — primary, full width when recording for a clear stop target */}
              <button
                onClick={onMic}
                disabled={pending && !recording}
                className={
                  "min-h-touch w-full rounded-2xl px-5 text-elder-base font-bold active:opacity-70 disabled:opacity-40 " +
                  (recording ? "bg-red-500 text-white" : "bg-tg-secondary-bg")
                }
              >
                {recording ? t("recording", lang) : t("tell_problem", lang)}
              </button>
              <div className="flex items-end gap-2">
                <label
                  aria-label={t("photo_hint", lang)}
                  className={
                    "flex min-h-touch shrink-0 items-center rounded-2xl bg-tg-secondary-bg px-4 text-2xl active:opacity-70 " +
                    (pending
                      ? "pointer-events-none opacity-40"
                      : "cursor-pointer")
                  }
                >
                  📷
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    hidden
                    disabled={pending}
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) onPhoto(f);
                      e.target.value = "";
                    }}
                  />
                </label>
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder={t("type_here", lang)}
                  rows={1}
                  className="min-h-touch flex-1 resize-none rounded-2xl bg-tg-secondary-bg px-4 py-3 text-elder-base outline-none"
                />
                <button
                  disabled={pending || !draft.trim()}
                  onClick={submit}
                  className="min-h-touch shrink-0 rounded-2xl bg-tg-button px-5 text-elder-base font-bold text-tg-button-text active:opacity-70 disabled:opacity-40"
                >
                  {t("send", lang)}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Bubble({
  role,
  text,
  image,
  muted,
}: {
  role: "bot" | "me";
  text: string;
  image?: string;
  muted?: boolean;
}) {
  const me = role === "me";
  return (
    <div className={me ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          "max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-elder-base " +
          (me
            ? "bg-tg-button text-tg-button-text"
            : "bg-tg-secondary-bg " + (muted ? "text-tg-hint" : ""))
        }
      >
        {image && (
          <img src={image} alt="" className="mb-2 max-h-60 rounded-xl" />
        )}
        {text}
      </div>
    </div>
  );
}
