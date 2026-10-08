FROM node:22-bookworm-slim AS build
WORKDIR /src
COPY nexus-control-frontend/package.json nexus-control-frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY nexus-control-frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY deploy/appliance/web/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/dist /srv
EXPOSE 80
