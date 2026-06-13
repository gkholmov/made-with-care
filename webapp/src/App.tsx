import { useCallback, useEffect, useState } from "react";
import { api, Me } from "./lib/api";
import { normLang, t } from "./lib/i18n";
import { tg } from "./lib/telegram";
import ElderHome from "./pages/elder/Home";
import Dashboard from "./pages/relative/Dashboard";
import ElderDetail from "./pages/relative/ElderDetail";
import SetupWizard from "./pages/relative/SetupWizard";
import Settings from "./pages/relative/Settings";
import Unknown from "./pages/Unknown";

export type Page =
  | { view: "dashboard" }
  | { view: "elder"; id: number }
  | { view: "settings"; id: number }
  | { view: "wizard" };

export default function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState(false);
  const [page, setPage] = useState<Page>({ view: "dashboard" });

  useEffect(() => {
    api
      .get<Me>("/api/me")
      .then(setMe)
      .catch(() => setError(true));
  }, []);

  const goBack = useCallback(() => {
    setPage((p) =>
      p.view === "settings"
        ? { view: "elder", id: p.id }
        : { view: "dashboard" },
    );
  }, []);

  useEffect(() => {
    const back = tg().BackButton;
    if (me?.role !== "elder" && page.view !== "dashboard") {
      back.show();
      back.onClick(goBack);
      return () => back.offClick(goBack);
    }
    back.hide();
  }, [page, me, goBack]);

  const lang = normLang(
    me?.language ?? tg().initDataUnsafe.user?.language_code,
  );

  if (error) return <Center>{t("error", lang)}</Center>;
  if (!me) return <Center>{t("loading", lang)}</Center>;

  if (me.role === "elder") return <ElderHome lang={lang} />;

  if (me.role === "unknown" && page.view !== "wizard")
    return <Unknown lang={lang} onSetup={() => setPage({ view: "wizard" })} />;

  switch (page.view) {
    case "elder":
      return (
        <ElderDetail
          lang={lang}
          elderId={page.id}
          onSettings={() => setPage({ view: "settings", id: page.id })}
        />
      );
    case "settings":
      return <Settings lang={lang} elderId={page.id} />;
    case "wizard":
      return (
        <SetupWizard
          lang={lang}
          onDone={() => setPage({ view: "dashboard" })}
        />
      );
    default:
      return (
        <Dashboard
          lang={lang}
          onOpen={(id) => setPage({ view: "elder", id })}
          onAdd={() => setPage({ view: "wizard" })}
        />
      );
  }
}

function Center({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-6 text-elder-base text-tg-hint">
      {children}
    </div>
  );
}
