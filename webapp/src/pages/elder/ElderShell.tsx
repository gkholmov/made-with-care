import { useEffect, useRef, useState } from "react";
import {
  api,
  Conversation as Conv,
  ElderHome,
  Reply,
  ReplyEnvelope,
} from "../../lib/api";
import { Lang, t } from "../../lib/i18n";
import { tg } from "../../lib/telegram";
import { useRecorder } from "../../lib/voice";
import Home from "./Home";
import Conversation, { Msg } from "./Conversation";

const TERMINAL = ["resolved", "escalated", "safety_stop"];

/** The elder's whole experience: the home launcher (topics, screen, call) is the
 * anchor; the chat conversation opens on top and is always one tap from Home. */
export default function ElderShell({ lang: fallbackLang }: { lang: Lang }) {
  const [home, setHome] = useState<ElderHome | null>(null);
  const [view, setView] = useState<"home" | "conversation">("home");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [reply, setReply] = useState<Reply | null>(null);
  const [pending, setPending] = useState(false);
  const recorder = useRecorder();
  const booted = useRef(false);

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    api
      .get<ElderHome>("/api/elder/home")
      .then(setHome)
      .catch(() => {});
    // Load any in-progress chat into the background, but stay on Home — the elder
    // sees the launcher first and taps "Continue" to re-enter the chat.
    api
      .get<Conv>("/api/elder/conversation")
      .then((c) => {
        if (c.active && c.turns.length) {
          setMessages(c.turns.map((tn) => ({ role: tn.role, text: tn.text })));
          setReply({
            text: "",
            state: c.state ?? "active",
            expect_confirm: !!c.expect_confirm,
            show_call: true,
          });
        }
      })
      .catch(() => {});
  }, []);

  const lang = (home?.language as Lang) || fallbackLang;
  const ongoing =
    messages.length > 0 && (!reply || !TERMINAL.includes(reply.state));

  // Every orchestrator round-trip flows through here.
  async function drive(fn: () => Promise<ReplyEnvelope>, mine?: Msg) {
    if (mine) setMessages((m) => [...m, mine]);
    setPending(true);
    try {
      const { reply: r } = await fn();
      setMessages((m) => [...m, { role: "bot", text: r.text }]);
      setReply(r);
    } catch {
      setMessages((m) => [...m, { role: "bot", text: t("conv_error", lang) }]);
    } finally {
      setPending(false);
    }
  }

  const startTopic = (key: string) => {
    setMessages([]);
    setReply(null);
    setView("conversation");
    void drive(() =>
      api.post<ReplyEnvelope>("/api/elder/topic", { name: key }),
    );
  };
  const sendMessage = (text: string) =>
    drive(() => api.post<ReplyEnvelope>("/api/elder/message", { text }), {
      role: "me",
      text,
    });
  const confirm = (yes: boolean) =>
    drive(
      () =>
        api.post<ReplyEnvelope>("/api/elder/message", {
          text: yes ? "yes" : "no",
        }),
      {
        role: "me",
        text: t(yes ? "conf_worked" : "conf_not_yet", lang),
      },
    );
  const sendPhoto = () => {
    setView("conversation");
    void drive(() => api.post<ReplyEnvelope>("/api/elder/photo", {}), {
      role: "me",
      text: t("conv_photo_sent", lang),
    });
  };

  // Voice: the transcript comes back from the server, so we append it after the call
  // (unlike text/buttons where the elder's words are known up front).
  async function sendVoice(clip: { b64: string; mime: string }) {
    setView("conversation");
    setPending(true);
    try {
      const res = await api.post<ReplyEnvelope>("/api/elder/voice", {
        audio_b64: clip.b64,
        mime: clip.mime,
      });
      if (res.transcript)
        setMessages((m) => [...m, { role: "me", text: res.transcript! }]);
      setMessages((m) => [...m, { role: "bot", text: res.reply.text }]);
      setReply(res.reply);
    } catch {
      setMessages((m) => [...m, { role: "bot", text: t("conv_error", lang) }]);
    } finally {
      setPending(false);
    }
  }

  const toggleMic = async () => {
    if (recorder.recording) {
      const clip = await recorder.stop();
      if (clip) await sendVoice(clip);
    } else {
      const ok = await recorder.start();
      if (!ok) {
        setView("conversation");
        setMessages((m) => [...m, { role: "bot", text: t("mic_error", lang) }]);
      }
    }
  };
  const callRelative = () => {
    if (home?.relative.telegram_id)
      tg().openTelegramLink(`tg://user?id=${home.relative.telegram_id}`);
  };
  const goHome = () => setView("home"); // keep the chat in the background
  const finish = () => {
    // conversation is over (or abandoned): clear it and return to the launcher
    setMessages([]);
    setReply(null);
    setView("home");
  };

  if (!home) {
    return (
      <div className="elder flex min-h-screen items-center justify-center text-elder-lg text-tg-hint">
        {t("loading", fallbackLang)}
      </div>
    );
  }

  if (view === "home") {
    return (
      <Home
        lang={lang}
        home={home}
        ongoing={ongoing}
        recording={recorder.recording}
        onResume={() => setView("conversation")}
        onTopic={startTopic}
        onMic={toggleMic}
        onPhoto={sendPhoto}
        onCall={callRelative}
      />
    );
  }

  return (
    <Conversation
      lang={lang}
      messages={messages}
      reply={reply}
      pending={pending}
      canCall={!!home.relative.telegram_id}
      relativeName={home.relative.name}
      recording={recorder.recording}
      onSend={sendMessage}
      onConfirm={confirm}
      onMic={toggleMic}
      onPhoto={sendPhoto}
      onCall={callRelative}
      onGoHome={goHome}
      onFinish={finish}
    />
  );
}
