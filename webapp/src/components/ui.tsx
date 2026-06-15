/** Shared UI primitives. Every tappable control in the app is built from these so
 * the look is consistent and predictable: always icon + text, fixed sizes, clear
 * pressed state, one color meaning per variant. */
import { ReactNode } from "react";

type Variant =
  | "primary"
  | "secondary"
  | "success"
  | "warn"
  | "danger"
  | "ghost";
type Size = "lg" | "md";

const VARIANT: Record<Variant, string> = {
  primary: "bg-tg-button text-tg-button-text",
  secondary: "bg-tg-secondary-bg text-tg-text",
  success: "bg-success text-success-text",
  warn: "bg-warn text-warn-text",
  danger: "bg-danger text-danger-text",
  ghost: "bg-tg-bg text-tg-button border-4 border-tg-button",
};

function shape(
  variant: Variant,
  size: Size,
  align: "center" | "start",
): string {
  return [
    "flex w-full items-center rounded-2xl px-5 font-bold active:opacity-70 disabled:opacity-40",
    size === "lg"
      ? "min-h-touch-lg text-elder-lg"
      : "min-h-touch text-elder-base",
    align === "center" ? "justify-center" : "justify-start gap-3 text-left",
    VARIANT[variant],
  ].join(" ");
}

export function ActionButton({
  icon,
  label,
  sublabel,
  variant = "secondary",
  size = "md",
  align = "center",
  disabled,
  onClick,
}: {
  icon?: string;
  label: string;
  sublabel?: string;
  variant?: Variant;
  size?: Size;
  align?: "center" | "start";
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={shape(variant, size, align)}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {icon && align === "center" && <span className="w-2" />}
      <span className="flex flex-col">
        <span>{label}</span>
        {sublabel && (
          <span className="text-elder-base font-normal opacity-80">
            {sublabel}
          </span>
        )}
      </span>
    </button>
  );
}

/** A photo control. Looks identical to an ActionButton but wraps a file input.
 * Without `capture`, the OS lets the elder take a photo OR pick from the gallery. */
export function PhotoPicker({
  icon = "📷",
  label,
  capture,
  size = "md",
  variant = "secondary",
  align = "center",
  disabled,
  onFile,
}: {
  icon?: string;
  label: string;
  capture?: boolean;
  size?: Size;
  variant?: Variant;
  align?: "center" | "start";
  disabled?: boolean;
  onFile: (file: File) => void;
}) {
  return (
    <label
      className={
        shape(variant, size, align) +
        (disabled ? " pointer-events-none opacity-40" : " cursor-pointer")
      }
    >
      <span className="shrink-0">{icon}</span>
      {align === "center" && <span className="w-2" />}
      <span>{label}</span>
      <input
        type="file"
        accept="image/*"
        {...(capture ? { capture: "environment" as const } : {})}
        hidden
        disabled={disabled}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
    </label>
  );
}

/** The identical top bar on every non-home screen: a clear way back + where you are. */
export function ScreenHeader({
  title,
  onBack,
  backLabel = "Home",
  right,
}: {
  title?: string;
  onBack?: () => void;
  backLabel?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 border-b border-line px-3 py-3">
      {onBack ? (
        <button
          onClick={onBack}
          className="min-h-12 shrink-0 rounded-xl bg-tg-secondary-bg px-4 text-elder-base font-semibold text-tg-button active:opacity-70"
        >
          ‹ {backLabel}
        </button>
      ) : (
        <span className="w-2" />
      )}
      {title && (
        <span className="flex-1 truncate text-center font-serif text-elder-base font-bold">
          {title}
        </span>
      )}
      <span className="min-h-12 shrink-0">{right}</span>
    </div>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="px-1 pt-2 text-sm font-bold uppercase tracking-wide text-tg-hint">
      {children}
    </p>
  );
}

export function Card({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick?: () => void;
}) {
  const cls = "rounded-2xl border border-line bg-tg-secondary-bg p-4";
  return onClick ? (
    <button
      onClick={onClick}
      className={cls + " w-full text-left active:opacity-70"}
    >
      {children}
    </button>
  ) : (
    <div className={cls}>{children}</div>
  );
}
