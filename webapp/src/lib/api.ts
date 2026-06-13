import { tg, isMock, devTgId } from "./telegram";

function authHeader(): string {
  const initData = tg().initData;
  if (initData) return `tma ${initData}`;
  if (isMock && devTgId) return `dev ${devTgId}`;
  return "";
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: {
      Authorization: authHeader(),
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body: unknown) => request<T>("POST", path, body),
  patch: <T>(path: string, body: unknown) => request<T>("PATCH", path, body),
};

// ---- response shapes (mirror ph/web/api.py) ----
export interface Me {
  role: "elder" | "relative" | "unknown";
  tg_id: number;
  name: string;
  language: string;
  elder_id?: number;
  relative_name?: string;
  bot_username: string;
}

export interface ElderHome {
  name: string;
  language: string;
  relative: { name: string; telegram_id: number | null };
  topics: { key: string; label: string }[];
  strings: { greeting_short: string; photo: string; call: string };
}

export type ReplyState =
  | "active"
  | "resolved"
  | "escalated"
  | "safety_stop"
  | "clarify";

export interface Reply {
  text: string;
  state: ReplyState;
  expect_confirm: boolean;
  show_call: boolean;
}

export interface ReplyEnvelope {
  reply: Reply;
}

export interface ConvTurn {
  role: "bot" | "me";
  text: string;
  modality: string;
}

export interface Conversation {
  active: boolean;
  state?: ReplyState;
  expect_confirm?: boolean;
  turns: ConvTurn[];
}

export interface ElderSummary {
  elder_id: number;
  name: string;
  language: string;
  claimed: boolean;
  last_event_at: string | null;
  open_alerts: number;
}

export interface ElderDetailData {
  elder_id: number;
  name: string;
  language: string;
  claimed: boolean;
  consent_at: string | null;
  phone_os: string;
  phone_age: string;
  join_link: string | null;
}

export interface SessionSummary {
  scenario: string;
  step: number;
  state: string;
  resolved: boolean;
  escalated: boolean;
  started_at: string;
}

export interface EventItem {
  type: string;
  meta: string;
  at: string;
}

export interface SetupResult {
  token: string;
  link: string | null;
}
