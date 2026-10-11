const PATHS: Record<string, React.ReactNode> = {
  agreement: (
    <>
      <path d="M7 4.5h7l4 4V19.5H7V4.5Z" strokeLinejoin="round" />
      <path d="M14 4.5V9h4.5M9.5 13h5M9.5 16.5h3" strokeLinecap="round" />
    </>
  ),
  deed: (
    <>
      <path d="M6 5h12v11a3 3 0 0 1-3 3H6V5Z" strokeLinejoin="round" />
      <path d="M9 9h6M9 12.5h6" strokeLinecap="round" />
      <path d="M18 16.5a2.5 2.5 0 0 1 0 5" strokeLinecap="round" />
    </>
  ),
  notice: (
    <>
      <path d="M12 4.5v15M7 8h10" strokeLinecap="round" />
      <path d="m7 8-3 6a3 3 0 0 0 6 0L7 8Zm10 0-3 6a3 3 0 0 0 6 0l-3-6Z" strokeLinejoin="round" />
    </>
  ),
  complaint: (
    <>
      <path d="M4.5 10 12 5l7.5 5M6 10v7M10 10v7M14 10v7M18 10v7M4.5 19.5h15" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  affidavit: (
    <>
      <path d="m5 18.5 1-4L16.5 4a1.8 1.8 0 0 1 2.5 2.5L8.5 17 5 18.5Z" strokeLinejoin="round" />
      <path d="M13 8l3 3M12 19.5h7" strokeLinecap="round" />
    </>
  ),
  application: (
    <>
      <rect x="6" y="5" width="12" height="15" rx="2" />
      <path d="M9.5 3.5h5v3h-5zM9 11h6M9 14.5h4" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
};

export default function CategoryIcon({ kind, className }: { kind: string; className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      {PATHS[kind] ?? PATHS.agreement}
    </svg>
  );
}
