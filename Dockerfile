# Stage 1: Build stage
FROM node:20-slim AS build

# Set the working directory
WORKDIR /app

# Copy package files and install dependencies
# Doing this before copying the full source code leverages Docker caching
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the app (if using TypeScript or a bundler)
RUN npm run build

# Stage 2: Production stage
FROM node:20-slim

WORKDIR /app

# Copy only the necessary files from the build stage
COPY --from=build /app/dist ./dist
COPY --from=build /app/package*.json ./
COPY --from=build /app/node_modules ./node_modules

# Use a non-root user for better security
USER node

# Expose the port the app runs on
EXPOSE 3000

# Define the command to run the app
CMD ["node", "dist/index.js"]
