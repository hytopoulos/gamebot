# GameBot

A FastMCP server that integrates with OpenAI's Vector Store for document search and retrieval, providing a robust API for game-related AI functionalities.

## ✨ Features

- **Natural Language Processing**: Search documents using natural language queries
- **Vector Store Integration**: Seamless integration with OpenAI's Vector Store
- **RESTful API**: Well-documented endpoints for easy integration
- **Containerized**: Ready for Docker deployment
- **Scalable**: Built with performance and scalability in mind
- **Health Monitoring**: Built-in health check endpoints

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [OpenAI API key](https://platform.openai.com/api-keys)
- (Optional) Vector Store ID from OpenAI
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) (for manual deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gamebot.git
   cd gamebot
   ```

2. **Set up environment variables**
   Copy the example environment file and update with your values:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and set your configuration:
   ```bash
   # Required
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional (if using vector store)
   VECTOR_STORE_ID=your_vector_store_id_here
   
   # Server configuration
   HOST=0.0.0.0
   PORT=8000
   ALLOWED_ORIGINS=*
   ```

3. **Set up a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the development server**
   ```bash
   python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```
   
   The API will be available at `http://localhost:8000`

5. **Test the API**
   ```bash
   # Health check
   curl -X POST http://localhost:8000/health_check -H "Content-Type: application/json" -d '{}'
   ```

## 🚀 Deployment

### GitHub Secrets Setup

1. **Set up required secrets in your GitHub repository**:
   - Go to your repository on GitHub
   - Navigate to Settings > Secrets and variables > Actions
   - Add the following repository secrets:
     - `HEROKU_API_KEY`: Your Heroku API key
     - `HEROKU_EMAIL`: Your Heroku account email
     - `HEROKU_APP_NAME`: Your Heroku app name
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `VECTOR_STORE_ID`: Your OpenAI Vector Store ID (if applicable)

### Automated Deployment with GitHub Actions

The repository includes a GitHub Actions workflow that automatically deploys to Heroku on every push to the `main` branch.

1. **Workflow file**: `.github/workflows/deploy.yml`
   - Installs Python dependencies
   - Runs tests
   - Deploys to Heroku using the configured secrets

2. **Manual deployment trigger**:
   ```bash
   git push origin main
   ```

### Local Development

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

2. **Run locally**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -m uvicorn server:app --reload
   ```

### 🐳 Docker Deployment (Optional)

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**
   ```bash
   docker build -t gamebot .
   docker run -p 8000:8000 --env-file .env gamebot
   ```

## 📚 API Documentation

### Health Check

```
POST /health_check
```

**Response**
```json
{
  "status": "ok",
  "timestamp": "2025-07-26T23:23:36.930670",
  "service": "gamebot",
  "version": "1.0.0"
}
```

## 🔧 Configuration

All configuration is done through environment variables. See `.env.example` for all available options.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for their amazing API
- FastMCP for the server framework
- All contributors who helped improve this project
   ```
   The server will be available at http://localhost:8000

### Using Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**
   ```bash
   docker build -t gamebot .
   docker run -p 8000:8000 -e OPENAI_API_KEY=your_key -e VECTOR_STORE_ID=your_id gamebot
   ```

## API Endpoints

- `POST /search`: Search for documents
  ```json
  {
    "query": "search terms"
  }
  ```

- `POST /fetch`: Fetch document by ID
  ```json
  {
    "id": "document_id"
  }
  ```

- `GET /health`: Health check endpoint

## Testing

Run the test suite:
```bash
make test
```

Run with coverage report:
```bash
pytest --cov=. --cov-report=html
```

## Advanced Deployment

### Docker Hub

1. Build and push the Docker image:
   ```bash
   docker build -t yourusername/gamebot:latest .
   docker push yourusername/gamebot:latest
   ```

2. Run in production:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e OPENAI_API_KEY=your_key \
     -e VECTOR_STORE_ID=your_id \
     -e ALLOWED_ORIGINS=https://yourdomain.com \
     --name gamebot \
     yourusername/gamebot:latest
   ```

### Kubernetes

Example deployment configuration (`k8s/deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gamebot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gamebot
  template:
    metadata:
      labels:
        app: gamebot
    spec:
      containers:
      - name: gamebot
        image: yourusername/gamebot:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gamebot-secrets
              key: openai-api-key
        - name: VECTOR_STORE_ID
          valueFrom:
            secretKeyRef:
              name: gamebot-secrets
              key: vector-store-id
---
apiVersion: v1
kind: Service
metadata:
  name: gamebot-service
spec:
  selector:
    app: gamebot
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `VECTOR_STORE_ID` | Yes | - | ID of your OpenAI Vector Store |
| `HOST` | No | `0.0.0.0` | Host to bind the server to |
| `PORT` | No | `8000` | Port to run the server on |
| `ALLOWED_ORIGINS` | No | `*` | Comma-separated list of allowed CORS origins |

## License

MIT
