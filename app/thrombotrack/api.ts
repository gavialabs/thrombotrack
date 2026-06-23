export const apiFetch = async (
  path: string,
  options: { [key: string]: any } = {},
): Promise<any> => {
  let body = options.body;
  const headers: { [key: string]: string } = {};

  if (!(body instanceof FormData)) {
    body = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${process.env.EXPO_PUBLIC_API_URL}${path}`, {
    ...options,
    body,
    credentials: "include", // include session cookie
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (res.status === 401) {
    // redirect to login
    window.location.href = `${process.env.EXPO_PUBLIC_API_URL}/auth/login`;
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `Request failed: ${res.status}`);
  }

  return res.json();
};
