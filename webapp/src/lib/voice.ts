import { useRef, useState } from "react";

/** In-app microphone recording via MediaRecorder. Returns base64 audio + mime so
 * the backend can transcribe it. Picks a format the platform supports (webm on
 * Android/Chrome, mp4 on iOS Safari / Telegram iOS webview). */
export function useRecorder() {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState(false);
  const rec = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const stream = useRef<MediaStream | null>(null);

  function pickMime(): string {
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/ogg",
    ];
    const MR = window.MediaRecorder;
    for (const c of candidates)
      if (MR && MR.isTypeSupported && MR.isTypeSupported(c)) return c;
    return "";
  }

  async function start(): Promise<boolean> {
    setError(false);
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      const mime = pickMime();
      rec.current = new MediaRecorder(
        stream.current,
        mime ? { mimeType: mime } : undefined,
      );
      chunks.current = [];
      rec.current.ondataavailable = (e) =>
        e.data.size && chunks.current.push(e.data);
      rec.current.start();
      setRecording(true);
      return true;
    } catch {
      setError(true);
      return false;
    }
  }

  /** Stop and return the recorded clip, or null if nothing was captured. */
  function stop(): Promise<{ b64: string; mime: string } | null> {
    return new Promise((resolve) => {
      const r = rec.current;
      if (!r) return resolve(null);
      r.onstop = async () => {
        stream.current?.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(chunks.current, {
          type: r.mimeType || "audio/webm",
        });
        if (!blob.size) return resolve(null);
        const buf = await blob.arrayBuffer();
        let bin = "";
        const bytes = new Uint8Array(buf);
        for (let i = 0; i < bytes.length; i++)
          bin += String.fromCharCode(bytes[i]);
        resolve({
          b64: btoa(bin),
          mime: (r.mimeType || "audio/webm").split(";")[0],
        });
      };
      r.stop();
    });
  }

  return { recording, error, start, stop };
}
