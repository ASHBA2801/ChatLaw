import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { PrismaAdapter } from "@auth/prisma-adapter";

import { prisma } from "@/lib/db/client";
import { getAuthConfiguration } from "@/lib/auth/config";

const authConfiguration = getAuthConfiguration();
const googleConfigured = authConfiguration.googleConfigured;

if (process.env.NODE_ENV === "production" && !authConfiguration.authSecretConfigured) {
  throw new Error("AUTH_SECRET must be configured with a stable random value in production.");
}

export const isGoogleAuthConfigured = googleConfigured;
export const authConfigurationStatus = authConfiguration;

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: process.env.AUTH_TRUST_HOST === "true" || process.env.NODE_ENV !== "production",
  adapter: PrismaAdapter(prisma as never),
  session: { strategy: "database" },
  pages: { signIn: "/signin" },
  providers: googleConfigured
    ? [
        Google({
          clientId: authConfiguration.googleClientId,
          clientSecret: authConfiguration.googleClientSecret,
        }),
      ]
    : [],
  callbacks: {
    session({ session, user }) {
      if (session.user) {
        session.user.id = user.id;
        session.user.preferredLanguage =
          (user as { preferredLanguage?: string | null }).preferredLanguage ?? "en";
      }
      return session;
    },
  },
});
