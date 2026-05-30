import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import { useState } from "react";

WebBrowser.maybeCompleteAuthSession();

const TENANT_ID = process.env.EXPO_PUBLIC_AZURE_TENANT_ID!;
const CLIENT_ID = process.env.EXPO_PUBLIC_AZURE_CLIENT_ID!;
const REDIRECT_URI = AuthSession.makeRedirectUri({ path: "oidc_callback" });

const discovery = {
  authorizationEndpoint: `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/authorize`,
  tokenEndpoint: `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token`,
};

console.log(REDIRECT_URI);

export function useAzureAuth() {
  const [user, setUser] = useState(null);

  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: CLIENT_ID,
      scopes: ["openid", "profile", "email"],
      redirectUri: REDIRECT_URI,
      responseType: AuthSession.ResponseType.Token, // implicit for web SPA
      usePKCE: true, // always use PKCE
    },
    discovery,
  );

  console.log("response", response);

  async function login() {
    const result = await promptAsync();

    if (result.type !== "success") return;

    console.log(result);

    const idToken = result.params.id_token ?? result.authentication?.idToken;

    console.log(idToken);

    // Send the ID token to your Flask backend
    // const res = await fetch("https://your-flask-api.com/api/auth/verify", {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify({ id_token: idToken }),
    // });

    // const data = await res.json();
    // if (res.ok) {
    //   setUser(data.user);
    //   // store data.session_token in SecureStore / localStorage for future requests
    // }
  }

  return { login, user, ready: !!request };
}
