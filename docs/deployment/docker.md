# Docker Deployment

## Single Node

```bash
docker run -d --name akasha \
  -p 7777:7777 \
  -p 50051:50051 \
  -v akasha-data:/data \
  alejandrosl/akasha:latest
```

## Docker Compose

```yaml
version: '3.8'
services:
  akasha:
    image: alejandrosl/akasha:latest
    ports:
      - "7777:7777"
      - "50051:50051"
    volumes:
      - akasha-data:/data
    environment:
      - AKASHA_AUTH_ENABLED=true
      - AKASHA_JWT_SECRET=your-secret
    restart: unless-stopped

volumes:
  akasha-data:
```

## Health Check

```bash
curl -s http://localhost:7777/api/v1/health | jq .status
# "ok"
```
