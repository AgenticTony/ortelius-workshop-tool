# Workshop Tool — frontend (Flutter web) image
#
# Multi-stage: build the Flutter web app in a SDK stage, then serve the
# static output from a tiny nginx image. Deployed as a Render static site
# (or any static host).

# ── Stage 1: build the web app ───────────────────────────────
# Pin the Flutter SDK to match the local dev version (3.38.6). Bump in
# lockstep when you upgrade Flutter locally.
FROM ghcr.io/cirruslabs/flutter:3.38.6 AS build

WORKDIR /app
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get

COPY . .
# The app reads .env as an asset; stub it so the build doesn't fail.
RUN cp .env.example .env
RUN flutter build web --release

# ── Stage 2: serve with nginx ────────────────────────────────
FROM nginx:alpine

# Flutter web is a single-page app — route everything to index.html so
# client-side routing (/join, /facilitate, etc.) works on refresh.
RUN printf 'server {\n\
  listen 80;\n\
  root /usr/share/nginx/html;\n\
  index index.html;\n\
  location / { try_files $uri $uri/ /index.html; }\n\
}\n' > /etc/nginx/conf.d/default.conf

COPY --from=build /app/build/web /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
