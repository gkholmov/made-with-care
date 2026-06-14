import { useEffect, useRef, useState } from "react";
import { Reply } from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { ActionButton, PhotoPicker, ScreenHeader } from "../../components/ui";

export type Msg = { role: "bot" | "me"; text: string; image?: string };

const TERMINAL = ["resolved", "escalated", "safety_stop"];

/** In-app conversation: a persistent header (always one tap back to Home), big chat
 * bubbles, and a calm, predictable input — two big answers plus a clearly-labeled
 * "other ways" row. */
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
  const [typing, setTyping] = useState(false); // is the text box revealed?
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages, pending]);

  const submit = () => {
    const text = draft.trim();
    if (!text || pending) return;
    setDraft("");
    setTyping(false);
    onSend(text);
  };

  const state = reply?.state ?? "active";
  const terminal = TERMINAL.includes(state);
  const statusKey =
    pendingKind === "photo"
      ? "status_sending_photo"
      : pendingKind === "voice"
        ? "transcribing"
        : "status_thinking";

  return (
    <div className="elder flex h-screen flex-col">
      <ScreenHeader
        title={topicTitle}
        onBack={onGoHome}
        backLabel={t("back_home", lang)}
      />

      {/* messages */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <div className="mx-auto flex max-w-md flex-col gap-3">
          {messages.map((m, i) => (
            <Bubble key={i} role={m.role} text={m.text} image={m.image} />
          ))}
          {pending && <Bubble role="bot" text={t(statusKey, lang)} muted />}
          <div ref={bottom} />
        </div>
      </div>

      {/* input */}
      <div className="border-t border-tg-secondary-bg bg-tg-bg px-3 py-3">
        <div className="mx-auto flex max-w-md flex-col gap-3">
          {terminal ? (
            <>
              {(state === "escalated" || state === "safety_stop") &&
                canCall && (
                  <ActionButton
                    variant="primary"
                    size="lg"
                    label={`📞 ${t("call", lang)} ${relativeName}`}
                    onClick={onCall}
                  />
                )}
              <ActionButton
                variant="secondary"
                size="md"
                label={t("back_home", lang)}
                onClick={onFinish}
              />
            </>
          ) : (
            <>
              {messages.length > 0 && (
                <div className="flex gap-3">
                  <div className="flex-1">
                    <ActionButton
                      variant="success"
                      size="lg"
                      label={t("conf_worked", lang)}
                      disabled={pending}
                      onClick={() => onConfirm(true)}
                    />
                  </div>
                  <div className="flex-1">
                    <ActionButton
                      variant="warn"
                      size="lg"
                      label={t("conf_not_yet", lang)}
                      disabled={pending}
                      onClick={() => onConfirm(false)}
                    />
                  </div>
                </div>
              )}

              {typing ? (
                <div className="flex items-end gap-2">
                  <textarea
                    autoFocus
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder={t("type_here", lang)}
                    rows={2}
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
              ) : (
                <>
                  <p className="px-1 text-elder-base font-semibold text-tg-hint">
                    {t("other_ways", lang)}
                  </p>
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <ActionButton
                        variant={recording ? "danger" : "secondary"}
                        size="md"
                        label={
                          recording ? t("recording", lang) : t("talk", lang)
                        }
                        disabled={pending && !recording}
                        onClick={onMic}
                      />
                    </div>
                    <div className="flex-1">
                      <PhotoPicker
                        variant="secondary"
                        size="md"
                        label={t("show", lang)}
                        disabled={pending}
                        onFile={onPhoto}
                      />
                    </div>
                    <div className="flex-1">
                      <ActionButton
                        variant="secondary"
                        size="md"
                        label={t("type_btn", lang)}
                        disabled={pending}
                        onClick={() => setTyping(true)}
                      />
                    </div>
                  </div>
                </>
              )}
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
