FROM node:20-alpine

WORKDIR /app

# Install Python for build tools
RUN apk add --no-cache python3 make g++

# Copy package files
COPY web/package*.json ./web/
COPY package*.json ./

# Install dependencies
RUN cd web && npm ci
RUN npm ci

# Copy all code
COPY . .

# Expose port
EXPOSE 5000

# Start web dashboard only
CMD ["npm", "start", "--prefix", "web"]
