export function ChatNavIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path
        d="M5 6.5A2.5 2.5 0 0 1 7.5 4h9A2.5 2.5 0 0 1 19 6.5v7a2.5 2.5 0 0 1-2.5 2.5H11l-4 3.5V16H7.5A2.5 2.5 0 0 1 5 13.5v-7Z"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function DocumentsNavIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M7 4.5h7l4 4V19.5H7V4.5Z" strokeLinejoin="round" />
      <path d="M14 4.5V9h4.5M9.5 13h5M9.5 16.5h5" strokeLinecap="round" />
    </svg>
  );
}

export function CasesNavIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4.5 8.5h15v10a1.5 1.5 0 0 1-1.5 1.5h-12A1.5 1.5 0 0 1 4.5 18.5v-10Z" strokeLinejoin="round" />
      <path d="M9 8.5V7a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1.5M4.5 12.5h15" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ResearchNavIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="11" cy="11" r="6.5" />
      <path d="m16 16 3.5 3.5" strokeLinecap="round" />
    </svg>
  );
}

export function AccountNavIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="9" r="3.25" />
      <path d="M5.5 19.5c1.6-3 3.8-4.5 6.5-4.5s4.9 1.5 6.5 4.5" strokeLinecap="round" />
    </svg>
  );
}
