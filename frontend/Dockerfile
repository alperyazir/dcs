# Stage 1: Build
FROM node:20-slim AS build-stage

WORKDIR /app

# Copy package files first for layer caching
COPY package*.json /app/

# Use npm ci for reproducible builds
RUN npm ci

# Copy source files
COPY ./ /app/

# Build argument for API URL
ARG VITE_API_URL=${VITE_API_URL}

# Build the application
RUN npm run build

# Stage 2: Production
FROM nginx:1-alpine AS production

# Copy built assets from build stage
COPY --from=build-stage /app/dist/ /usr/share/nginx/html

# Copy nginx configuration
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
