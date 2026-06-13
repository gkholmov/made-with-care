/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_MOCK_TMA?: string;
  readonly VITE_DEV_TG_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
