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
import Home from "./Home";
import Conversation, { Msg } from "./Conversation";

/** The elder's whole experience lives here: topic launcher (Home) and the in-app
 * conversation. Nothing bounces back to the Telegram chat (except an emergency call). */
export default function ElderShell({ lang: fallbackLang }: { lang: Lang }) {
  const [home, setHome] = useState<ElderHome | null>(null);
  const [view, setView] = useState<"home" | "conversation">("home");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [reply, setReply] = useState<Reply | null>(null);
  const [pending, setPending] = useState(false);
  const booted = useRef(false);

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    api
      .get<ElderHome>("/api/elder/home")
      .then(setHome)
      .catch(() => {});
    // Resume an in-progress conversation if there is one.
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
          setView("conversation");
        }
      })
      .catch(() => {});
  }, []);

  const lang = (home?.language as Lang) || fallbackLang;

  // Every orchestrator round-trip flows through here: show my bubble, show typing,
  // then append the bot's reply and let it drive the input bar.
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
  const callRelative = () => {
    if (home?.relative.telegram_id)
      tg().openTelegramLink(`tg://user?id=${home.relative.telegram_id}`);
  };
  const backHome = () => {
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
        onTopic={startTopic}
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
      onSend={sendMessage}
      onConfirm={confirm}
      onPhoto={sendPhoto}
      onCall={callRelative}
      onBackHome={backHome}
    />
  );
}
