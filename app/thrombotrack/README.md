# ThromboTrack Frontend

This is an [Expo](https://expo.dev) project created with [`create-expo-app`](https://www.npmjs.com/package/create-expo-app).

## Prerequisites

- Node v20.18.0+
- npm installed

## Get Started

1. Install dependencies

   ```bash
   npm install
   ```
2. Copy `.env.example` to `.env`
3. Fill out `EXPO_PUBLIC_AZURE_TENANT_ID` and `EXPO_PUBLIC_AZURE_CLIENT_ID` in `.env`
3. Start the app

   ```bash
   npx expo start
   ```

In the output, you'll find options to open the app in a

- [development build](https://docs.expo.dev/develop/development-builds/introduction/)
- [Android emulator](https://docs.expo.dev/workflow/android-studio-emulator/)
- [iOS simulator](https://docs.expo.dev/workflow/ios-simulator/) -- recommended so that you can use the annotation canvas, which relies on touch events
- [Expo Go](https://expo.dev/go), a limited sandbox for trying out app development with Expo

This project uses [file-based routing](https://docs.expo.dev/router/introduction).

## Running on Your Own Device

Instead of using an emulator, if you want to run on your own device, you should be able to:
1. Find your laptop's local IP address (on Mac you can hold option and click the Wi-Fi icon)
2. Connect to the same network on your mobile device
3. Using a web browser, open your laptop's local IP address :8081

However, if you are on a network that enforces HTTPS connections (such as **eduroam**), or if you cannot connect to the same network on your mobile device, you can do the following:
1. Download and install [ngrok](https://ngrok.com/download)
2. Get a public URL for port 5000 (for the API)
   ```bash
   ngrok http 5000
   ```
3. Get a public URL for port 8081:
   ```bash
   ngrok http 8081
   ```
4. Copy the ngrok public URL for port 5000 into `.env` for `EXPO_PUBLIC_API_URL`
5. Copy the ngrok public URL for port 8081 into `/api/app/__init__.py` under CORS origins
6. Copy both public URLs into `/api/.env` under `FRONTEND_URL` and `API_URL`
7. Start the API (in `/api`)
   ```bash
   make up
   ```
8. Start the Expo app
   ```bash
   npx expo start
   ```

Now, you should be able to open the ngrok public URL for port 8081 on your mobile device and use the app. If you are able to connect to Expo but the API requests are not loading, try adding/removing a forward slash from the end of the public URL under the CORS configuration.

## Project Structure

```
.
├── app/                      # Screens for app (see file-based routing link above)
│   └── (logged-in)/          # Screen group only visible when the user is logged in
├── assets/                   # Icons and logos
├── components/               # React components used in screens
├── constants/                # Types and colors
├── context/                  # Global states
├── helpers.ts                # Helper files
├── app.json                  # Expo app configuration
└── package.json              # Dependencies
```

## Suggested Documentation

- [Expo documentation](https://docs.expo.dev/): Learn fundamentals, or go into advanced topics with our [guides](https://docs.expo.dev/guides).
- [Learn Expo tutorial](https://docs.expo.dev/tutorial/introduction/): Follow a step-by-step tutorial where you'll create a project that runs on Android, iOS, and the web.
- [React Native documentation](https://reactnative.dev)
- [TypeScript documentation](https://www.typescriptlang.org/docs/)
- [Expo vector icons list](https://icons.expo.fyi/Index)
