# Stage 1: Build the React application
FROM node:lts-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm ci 

COPY . .
RUN npm run build

# Stage 2: Serve the React application with Nginx
FROM nginx:alpine as production-stage

COPY --from=build-stage /app/build /usr/share/nginx/html

# Optional: Copy a custom Nginx configuration if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]