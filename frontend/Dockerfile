# Build stage
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Run build to produce production bundle in /app/dist
RUN npm run build

# Production web server stage
FROM nginx:alpine

# Copy custom nginx config or default
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
