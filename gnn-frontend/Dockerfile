# Stage 1: Build the React application with Vite
FROM node:20-alpine as build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code (including .env)
COPY . .

# Set build-time environment variable for Vite
ARG VITE_API_URL=https://oil-gnn-api-1072886277511.us-central1.run.app
ENV VITE_API_URL=${VITE_API_URL}

# Build the app (Vite outputs to /dist)
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine as production-stage

# Copy built files from dist directory (Vite build output)
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Create nginx config for SPA routing
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
    try_files $uri $uri/ /index.html; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]