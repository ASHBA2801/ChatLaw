import "server-only";

const PLACEHOLDER_VALUES = ["replace-with", "your-", "changeme", "todo"];

function isUsableSecret(value: string | undefined): value is string {
  if (!value?.trim()) return false;
  const normalized = value.trim().toLowerCase();
  return value.trim().length >= 32 && !PLACEHOLDER_VALUES.some((item) => normalized.includes(item));
}

export type AuthConfiguration = {
  authSecretConfigured: boolean;
  googleConfigured: boolean;
  googleClientId?: string;
  googleClientSecret?: string;
  issues: string[];
};

export function getAuthConfiguration(source: Partial<NodeJS.ProcessEnv> = process.env): AuthConfiguration {
  const authSecretConfigured = isUsableSecret(source.AUTH_SECRET);
  const googleClientId = source.AUTH_GOOGLE_ID?.trim() || undefined;
  const googleClientSecret = source.AUTH_GOOGLE_SECRET?.trim() || undefined;
  const issues: string[] = [];

  if (!authSecretConfigured) {
    issues.push("AUTH_SECRET is missing or is still a placeholder. Use a stable random value of at least 32 characters.");
  }
  if (!googleClientId || !googleClientSecret) {
    issues.push("AUTH_GOOGLE_ID and AUTH_GOOGLE_SECRET are required for Google sign-in.");
  }

  return {
    authSecretConfigured,
    googleConfigured: Boolean(googleClientId && googleClientSecret && authSecretConfigured),
    googleClientId,
    googleClientSecret,
    issues,
  };
}

export function safeCallbackUrl(value: string | undefined, fallback = "/documents"): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return fallback;
  return value;
}