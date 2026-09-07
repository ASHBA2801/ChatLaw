import { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      preferredLanguage?: string | null;
    } & DefaultSession["user"];
  }

  interface User {
    preferredLanguage?: string | null;
  }
}
