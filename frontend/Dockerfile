FROM node:22-alpine AS dependencies
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY frontend ./
ARG BACKEND_URL=http://backend:8000
ARG ADJUST_FRONTEND_URL=http://adjust-frontend:3002
ENV BACKEND_URL=$BACKEND_URL ADJUST_FRONTEND_URL=$ADJUST_FRONTEND_URL NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup -S civicforge && adduser -S civicforge -G civicforge
COPY --from=builder --chown=civicforge:civicforge /app/.next/standalone ./
COPY --from=builder --chown=civicforge:civicforge /app/.next/static ./.next/static
COPY --from=builder --chown=civicforge:civicforge /app/public ./public
USER civicforge
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s CMD node -e "fetch('http://127.0.0.1:3000/api/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"
CMD ["node", "server.js"]
