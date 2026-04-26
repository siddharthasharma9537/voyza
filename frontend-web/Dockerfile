FROM node:20-bookworm-slim

WORKDIR /app

# Copy only package files first
COPY package.json package-lock.json ./

# Install dependencies with build tools for native modules
RUN npm ci --include=optional --legacy-peer-deps

# Copy the rest of the source code
COPY --chown=node:node . .

EXPOSE 3000

ENV NEXT_PUBLIC_API_URL=http://api:8000/api/v1

USER node

CMD ["npm", "run", "dev"]
