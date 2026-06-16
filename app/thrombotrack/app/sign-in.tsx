import { FC } from "react";

/**
 * Dummy component for logged-out users.
 *
 * Shows empty content while the user ID is fetched (AuthContext.ts) and the user is appropriately
 * redirected to the API to log in (api.ts).
 *
 * @returns null
 */
const SignIn: FC = (): null => {
  return null;
};

export default SignIn;
