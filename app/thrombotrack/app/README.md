# App Screens

This is the directory for the app screens using Expo Router's [file-based routing](https://docs.expo.dev/router/introduction). The file names correspond to the actual URL path; `annotate.tsx` is hosted at `/annotate`, etc. There are a few things to note:

- Paranthesized directories are "groups" that do not change the URL path, but are conditionally displayed
  - In this app, `(logged-in)` corresponds to the screens that only display for logged-in users. This logic is handled in the top-level `_layout.tsx`
- `_layout.tsx` is the entrypoint for each group of screens-- this is where the routing logic and screen configuration is done
- `+html.tsx` is for web use only and defines the HTML skeleton container that the rest of the app is under (like the literal `<html>` and `<body>` tags, and any metadata)