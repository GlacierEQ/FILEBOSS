# Security Policy

## Supported Versions

We provide security updates for the following versions of DeepSeek-Coder:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of DeepSeek-Coder seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do not disclose the vulnerability publicly**
2. **Email us** at security@deepseek.com with details about the vulnerability
3. Include the following information:
   - Type of vulnerability
   - Full path of source file(s) related to the vulnerability
   - Location of the affected source code (tag/branch/commit or direct URL)
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the vulnerability

## What to expect

- We will acknowledge receipt of your report within 48 hours
- We will provide an initial assessment of the report within 7 days
- We aim to release a fix within 30 days, depending on complexity
- We will keep you informed about the progress of the fix
- Once the vulnerability is fixed, we will publicly acknowledge your responsible disclosure, unless you prefer to remain anonymous

## Security Measures

DeepSeek-Coder implements the following security measures:

- Regular dependency updates and vulnerability scanning
- Code reviews for security issues
- Input validation and output sanitization
- API authentication and rate limiting
- Secure Docker configuration with least privilege principles
- Robust data backup and recovery procedures

## Security FAQ

**Q: Is my code data sent to your servers when using DeepSeek-Coder?**  
A: No, when running locally or self-hosted, your code stays on your infrastructure. The API service processes all code within your deployment boundary.

**Q: Does DeepSeek-Coder include telemetry?**  
A: By default, anonymous usage statistics are collected to help improve the product. This can be disabled by setting `ENABLE_TELEMETRY=false` in your configuration.

**Q: How are API keys stored?**  
A: API keys are stored as environment variables and never persisted to disk in plain text.

## Best Practices

When deploying DeepSeek-Coder in production:

1. Use HTTPS for all API communications
2. Implement proper API authentication
3. Configure network security to restrict access to the service
4. Regularly update to the latest version
5. Run the service with minimal required permissions
6. Enable security logging and monitoring
