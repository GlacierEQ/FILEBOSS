# Verify the Deployment

This document provides instructions on how to verify the deployment of the FILEBOSS application.

## 1. Verify the Backend

*   **Check the application logs:** SSH into the EC2 instance and check the application logs for any errors:
    ```bash
    tail -f /var/log/fileboss.out.log
    tail -f /var/log/fileboss.err.log
    ```
*   **Check the application status:** Access the health check endpoint in your browser or using `curl`:
    ```bash
    curl http://your-domain.com/health
    ```
    You should see a response with `{"status": "ok"}`.

## 2. Verify the Frontend

*   **Access the application:** Open your browser and navigate to `http://your-domain.com`. You should see the FILEBOSS login page.
*   **Test the application:** Log in to the application and test the core features, such as creating a case, uploading a document, and adding evidence.

## 3. Run Integration Tests

*   **Run the integration test suite:** From your local machine, run the integration test suite against the live server:
    ```bash
    pytest tests/ --base-url http://your-domain.com
    ```
    All tests should pass.
