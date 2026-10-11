import Image from "next/image";
import Link from "next/link";

/** ChatLaw wordmark with the app logo (same artwork as the favicon). Used by the landing page, sign-in and the product shell. */
export default function BrandMark({
  href = "/",
  hideLabelOnMobile = false,
  size = "md",
  labelClassName = "",
}: {
  href?: string;
  hideLabelOnMobile?: boolean;
  size?: "sm" | "md";
  /** Extra classes for the wordmark, e.g. to hide it in a collapsed sidebar. */
  labelClassName?: string;
}) {
  const logo = size === "sm" ? "h-7 w-7" : "h-9 w-9";
  return (
    <Link href={href} className="flex min-w-0 items-center gap-2.5 rounded-lg font-semibold tracking-tight">
      <Image
        src="/ChatLaw Logo.png"
        alt=""
        width={72}
        height={72}
        priority
        className={`${logo} shrink-0 rounded-full object-contain`}
      />
      <span className={`truncate text-[15px] ${hideLabelOnMobile ? "hidden sm:inline" : ""} ${labelClassName}`}>ChatLaw</span>
    </Link>
  );
}
