export const apiFetch = async (
  path: string,
  options: { [key: string]: any } = {},
): Promise<any> => {
  const res = await fetch(`${process.env.EXPO_PUBLIC_API_URL}${path}`, {
    ...options,
    credentials: "include", // include session cookie
    headers: {
      "Content-Type": "application/json",
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
