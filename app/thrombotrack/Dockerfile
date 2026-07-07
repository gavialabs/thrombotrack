# Use Python base image
FROM node:26.4-alpine3.24

ARG APP_PORT

# Set working directory
WORKDIR /thrombotrack-app

# Install system dependencies
RUN apk add --no-cache bash git

# Copy requirements and install dependencies
COPY package*.json .
RUN npm install

# Copy application code
COPY . .

# Metro Bundler ports
EXPOSE ${APP_PORT}

## Exec
## When writing in the preferred json exec form, docker executes without a shell
## layer, and thus unable to expand the variable.
#CMD ["npm", "exec", "expo", "start", "--port", ${APP_PORT}]

# Need the extra -- to tell npm to stop parsing options and pass the remaining
# args directly to the underlying CLI tool.
CMD npm exec expo start -- --port ${APP_PORT}