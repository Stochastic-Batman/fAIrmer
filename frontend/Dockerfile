FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/build ./build
EXPOSE 3000
ENV PORT=3000
CMD ["node", "build"]
