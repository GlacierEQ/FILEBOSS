module.exports = {
  // Environment configurations
  environments: {
    local: {
      baseUrl: 'http://localhost:8000',
      auth: {
        type: 'basic',
        basic: {
          username: '${env.HTTPYAC_USER:-admin}',
          password: '${env.HTTPYAC_PASSWORD:-password}'
        }
      }
    },
    staging: {
      baseUrl: 'https://staging.fileboss.example.com',
      auth: {
        type: 'bearer',
        token: '${env.STAGING_TOKEN}'
      }
    },
    production: {
      baseUrl: 'https://api.fileboss.example.com',
      auth: {
        type: 'bearer',
        token: '${env.PRODUCTION_TOKEN}'
      }
    }
  },
  
  // Request/response settings
  request: {
    timeout: 10000, // 10 seconds
    rejectUnauthorized: true,
    followRedirect: true,
    maxRedirects: 5
  },
  
  // Test settings
  test: {
    timeout: 5000,
    expect: {
      statusCode: 200,
      contentType: 'application/json',
      maxSize: 1000000 // 1MB
    }
  },
  
  // Documentation settings
  documentation: {
    output: './docs/api',
    format: 'html',
    theme: 'dark',
    includeRequest: true,
    includeResponse: true,
    includeTests: true
  },
  
  // Logging
  log: {
    level: 'info',
    request: true,
    response: true,
    testResults: true
  },
  
  // Plugins
  plugins: [
    '@httpyac/plugin-json',
    '@httpyac/plugin-xml',
    '@httpyac/plugin-yaml'
  ]
};
