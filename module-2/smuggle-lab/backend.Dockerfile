FROM node:20-alpine
WORKDIR /app
COPY backend.js /app/backend.js
EXPOSE 8081
CMD ["node", "backend.js"]
