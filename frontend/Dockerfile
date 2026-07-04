# Workshop Tool — frontend (Flutter web) image
#
# Multi-stage: build the Flutter web app, then serve the static output from
# a tiny nginx image. We install Flutter from the official tarball rather
# than using a third-party SDK image (the CirrusLabs image hit
# pub.dev auth failures in CI).

# ── Stage 1: build the web app ───────────────────────────────
FROM debian:bookworm-slim AS build

# Flutter needs: curl + unzip to fetch the SDK, git (pub uses it), xz-utils
# to extract the tarball, and the standard web toolchain.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git unzip xz-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV FLUTTER_VERSION=3.44.4
ENV PATH="/opt/flutter/bin:${PATH}"

# Install Flutter from the official tarball (no third-party image).
# The tarball extracts to /opt/flutter directly, so no mv needed.
# 3.44.4 is the current stable Linux release — verify the version exists in
# releases_linux.json before changing FLUTTER_VERSION (not all versions are
# published as Linux tarballs).
RUN curl -fsSL https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${FLUTTER_VERSION}-stable.tar.xz \
    | tar -xJ -C /opt \
    && git config --global --add safe.directory /opt/flutter \
    && flutter --version

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
