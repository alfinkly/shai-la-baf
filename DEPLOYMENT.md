# Zoom RTMS Integration Example

## Zoom App Configuration

To integrate with Zoom, you need to create a Zoom App with WebSocket capabilities:

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Create a new app (Webhook-only or SDK app)
3. Enable real-time meeting transcript features
4. Configure WebSocket endpoints

## Example Zoom RTMS Configuration

```json
{
  "webhook_url": "ws://your-server:8000/ws/transcript",
  "events": [
    "meeting.transcript.started",
    "meeting.transcript.ended", 
    "meeting.transcript.updated"
  ]
}
```

## Example transcript message format from Zoom:

```json
{
  "participant_id": "user_12345",
  "participant_name": "John Smith",
  "text": "We need to complete the quarterly report by Friday",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Integration with Jira via MCP

The `/tasks` endpoint returns data in a format ready for Jira integration:

```bash
# Get tasks from our service
curl http://localhost:8000/tasks

# Use with MCP Jira to create tickets
# Example MCP command (adjust according to your MCP setup):
# mcp-jira create-issue --summary "Task Title" --description "Task Description"
```

## Production Deployment

### Option 1: Docker
```bash
docker build -t zoom-transcript-extractor .
docker run -p 8000:8000 --env-file .env zoom-transcript-extractor
```

### Option 2: Docker Compose
```bash
docker-compose up -d
```

### Option 3: Traditional deployment
```bash
./start.sh
```

## Security Considerations

- Always use HTTPS in production
- Validate Zoom webhook signatures
- Use proper authentication for the API endpoints
- Consider rate limiting for the WebSocket endpoint