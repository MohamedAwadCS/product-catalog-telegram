FROM node:24-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV API_URL=http://api:8000
RUN npm run build

CMD ["npm", "start"]