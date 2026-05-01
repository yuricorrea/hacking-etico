FROM node:20-alpine

WORKDIR /app

COPY package.json /app/package.json
RUN npm install --omit=dev --no-audit --no-fund

COPY server.js /app/server.js

EXPOSE 4000
CMD ["node", "server.js"]
