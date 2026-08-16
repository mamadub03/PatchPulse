# ---------- Stage 1: Build React ----------
FROM node:22-alpine AS build

WORKDIR /frontend

# Copy dependency files first for Docker caching
COPY package.json package-lock.json ./

RUN npm ci

# Now copy frequently-changing source
COPY . .

# Vite variables are used while building the frontend
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build


# ---------- Stage 2: Serve React ----------
FROM nginx:alpine

# Copy ONLY the finished frontend from the build stage
COPY --from=build /frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]