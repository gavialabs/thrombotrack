import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import { useState } from "react";

WebBrowser.maybeCompleteAuthSession();

const TENANT_ID = process.env.EXPO_PUBLIC_AZURE_TENANT_ID!;
const CLIENT_ID = process.env.EXPO_PUBLIC_AZURE_CLIENT_ID!;
const REDIRECT_URI = AuthSession.makeRedirectUri({ path: "oidc_callback" });

// const discovery = {
//   authorizationEndpoint: `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/authorize`,
//   tokenEndpoint: `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token`,
// };

export function useAzureAuth() {
  const [user, setUser] = useState(null);
  const discovery = AuthSession.useAutoDiscovery(
    `https://login.microsoftonline.com/${TENANT_ID}/v2.0`,
  );

  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: CLIENT_ID,
      scopes: ["openid", "profile", "email", "offline_access"],
      redirectUri: REDIRECT_URI,
      // code flow will prompt duo and give the correct id token
      responseType: AuthSession.ResponseType.Token,
    },
    discovery,
  );

  const login = async (): Promise<string | null> => {
    if (request === null) {
      return null;
    }

    const result = await promptAsync({ windowFeatures: { popup: false } });

    if (result.type !== "success") {
      return null;
    }

    console.log(request);
    console.log(result);

    const tokenResponse = await AuthSession.exchangeCodeAsync(
      {
        code: result.params.code,
        clientId: CLIENT_ID,
        redirectUri: REDIRECT_URI,
        extraParams: {
          code_verifier: request.codeVerifier!,
        },
      },
      discovery!,
    );

    console.log(tokenResponse);

    // Send the ID token to your Flask backend
    const res = await fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/auth/verify`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: result.params.code }),
      },
    );

    const data = await res.json();
    console.log(data);
    // if (res.ok) {
    //   setUser(data.user);
    //   // store data.session_token in SecureStore / localStorage for future requests
    // }

    throw new Error();

    return "test";
  };

  const loginTest = async (): Promise<string | null> => {
    if (request === null) {
      return null;
    }

    // Send the ID token to your Flask backend
    const res = await fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/auth/verify`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: "test" }),
      },
    );

    const data = await res.json();
    return data.session_token;
  };

  return { login, loginTest, user, ready: !!request };
}
