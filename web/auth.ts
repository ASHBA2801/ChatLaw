import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { PrismaAdapter } from "@auth/prisma-adapter";

import { prisma } from "@/lib/db/client";
import { getAuthConfiguration } from "@/lib/auth/config";

const authConfiguration = getAuthConfiguration();
const googleConfigured = authConfiguration.googleConfigured;

export const isGoogleAuthConfigured = googleConfigured;
export const authConfigurationStatus = authConfiguration;

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
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
