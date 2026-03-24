import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        username: { label: "Usuário", type: "text" },
        password: { label: "Senha", type: "password" },
      },
      async authorize(credentials) {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/v1/auth/login`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username: credentials.username,
              password: credentials.password,
            }),
          }
        );

        if (!res.ok) return null;

        const data = await res.json();
        return {
          id: data.user.id,
          name: data.user.display_name,
          email: data.user.email,
          username: data.user.username,
          is_admin: data.user.is_admin,
          access_token: data.access_token,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.access_token = (user as any).access_token;
        token.is_admin = (user as any).is_admin;
        token.username = (user as any).username;
      }
      return token;
    },
    async session({ session, token }) {
      (session.user as any).access_token = token.access_token;
      (session.user as any).is_admin = token.is_admin;
      (session.user as any).username = token.username;
      return session;
    },
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  session: { strategy: "jwt" },
});
