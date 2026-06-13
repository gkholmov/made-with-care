/** Thin wrapper over the Telegram WebApp SDK, with a dev mock so the app can
 * run in a plain browser (`VITE_MOCK_TMA=1 VITE_DEV_TG_ID=2002 npm run dev`). */

export interface TgWebApp {
  initData: string;
  initDataUnsafe: {
    user?: { id: number; first_name?: string; language_code?: string };
  };
  ready(): void;
  expand(): void;
  close(): void;
  sendData(data: string): void;
  openTelegramLink(url: string): void;
  BackButton: {
    show(): void;
    hide(): void;
    onClick(cb: () => void): void;
    offClick(cb: () => void): void;
  };
  MainButton: {
    setText(t: string): void;
    show(): void;
    hide(): void;
    enable(): void;
    disable(): void;
    showProgress(): void;
    hideProgress(): void;
    onClick(cb: () => void): void;
    offClick(cb: () => void): void;
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp: TgWebApp };
  }
}

const MOCK = import.meta.env.VITE_MOCK_TMA === "1";

function makeMock(): TgWebApp {
  const noop = () => {};
  const devId = Number(import.meta.env.VITE_DEV_TG_ID || "0");
  return {
    initData: "",
    initDataUnsafe: {
      user: { id: devId, first_name: "Dev", language_code: "en" },
    },
    ready: noop,
    expand: noop,
    close: () => console.log("[mock] close()"),
    sendData: (d) => console.log("[mock] sendData:", d),
    openTelegramLink: (u) => console.log("[mock] openTelegramLink:", u),
    BackButton: { show: noop, hide: noop, onClick: noop, offClick: noop },
    MainButton: {
      setText: (t) => console.log("[mock] MainButton:", t),
      show: noop,
      hide: noop,
      enable: noop,
      disable: noop,
      showProgress: noop,
      hideProgress: noop,
      onClick: noop,
      offClick: noop,
    },
  };
}

let cached: TgWebApp | null = null;

export function tg(): TgWebApp {
  if (!cached) {
    cached =
      !MOCK && window.Telegram?.WebApp ? window.Telegram.WebApp : makeMock();
  }
  return cached;
}

export const isMock = MOCK;
export const devTgId = import.meta.env.VITE_DEV_TG_ID || "";
