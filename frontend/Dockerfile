FROM node:22-alpine AS builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/. .
COPY api/openapi.json /app/api/openapi.json
ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=$SENTRY_RELEASE
RUN --mount=type=secret,id=SENTRY_URL \
    --mount=type=secret,id=SENTRY_AUTH_TOKEN \
    --mount=type=secret,id=SENTRY_ORG \
    --mount=type=secret,id=SENTRY_PROJECT \
    SENTRY_URL=$(cat /run/secrets/SENTRY_URL) \
    SENTRY_AUTH_TOKEN=$(cat /run/secrets/SENTRY_AUTH_TOKEN) \
    SENTRY_ORG=$(cat /run/secrets/SENTRY_ORG) \
    SENTRY_PROJECT=$(cat /run/secrets/SENTRY_PROJECT) \
    npm run build

FROM nginx:alpine
RUN apk add --no-cache openssl curl
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
ENTRYPOINT ["/docker-entrypoint.sh"]
