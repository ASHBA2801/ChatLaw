type IconProps = { className?: string };

function Svg({ className, children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {children}
    </svg>
  );
}

export function PinIcon({ className }: IconProps) {
  return <Svg className={className}><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z" /><circle cx="12" cy="10" r="2.3" /></Svg>;
}

export function PrintIcon({ className }: IconProps) {
  return <Svg className={className}><path d="M7 9V4.5h10V9M7 17H5a1.5 1.5 0 0 1-1.5-1.5v-5A1.5 1.5 0 0 1 5 9h14a1.5 1.5 0 0 1 1.5 1.5v5A1.5 1.5 0 0 1 19 17h-2" /><path d="M7 14h10v5.5H7z" /></Svg>;
}

export function MailIcon({ className }: IconProps) {
  return <Svg className={className}><rect x="3.5" y="5.5" width="17" height="13" rx="1.5" /><path d="m4 7 8 6 8-6" /></Svg>;
}

export function CopyIcon({ className }: IconProps) {
  return <Svg className={className}><rect x="8.5" y="8.5" width="11" height="11" rx="1.5" /><path d="M15.5 8.5V6A1.5 1.5 0 0 0 14 4.5H6A1.5 1.5 0 0 0 4.5 6v8A1.5 1.5 0 0 0 6 15.5h2.5" /></Svg>;
}

export function DownloadIcon({ className }: IconProps) {
  return <Svg className={className}><path d="M12 4.5v10M7.5 10.5 12 15l4.5-4.5M5 19.5h14" /></Svg>;
}

export function ExternalIcon({ className }: IconProps) {
  return <Svg className={className}><path d="M13.5 4.5h6v6M19.5 4.5 11 13M17 14v4.5A1 1 0 0 1 16 19.5H5.5a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1H10" /></Svg>;
}

export function ShieldIcon({ className }: IconProps) {
  return <Svg className={className}><path d="M12 3.5 5 6.5v5c0 4.4 3 8 7 9 4-1 7-4.6 7-9v-5l-7-3Z" /></Svg>;
}

export function ScalesIcon({ className }: IconProps) {
  return <Svg className={className}><path d="M12 4v16M7 20h10M5 7h14M5 7l-2.5 6a2.5 2.5 0 0 0 5 0L5 7ZM19 7l-2.5 6a2.5 2.5 0 0 0 5 0L19 7Z" /></Svg>;
}

export function CheckIcon({ className }: IconProps) {
  return <Svg className={className}><path d="m5 12.5 4.5 4.5L19 7.5" /></Svg>;
}
