# Backend Service

This FastAPI service hosts the LangGraph-based conversational agent that powers the website widget.

## Key Modules

- `app/api/`: HTTP and WebSocket routes for chat sessions and health checks.
- `app/agents/`: LangGraph graph definition and supporting nodes.
- `app/services/`: Integrations such as Discord notifications and scheduling APIs.
- `app/retrieval/`: Document ingestion pipeline and vector store utilities.
- `app/models/`: Pydantic schemas shared across modules.
- `app/config/`: Settings management and environment loading.

## Running Locally

```bash
uvicorn app.main:app --reload
```

Before running, create a `.env` file (see `app/config/settings.py`) with credentials for:

- OpenAI (or alternative LLM provider)
- Vector store settings (`CHROMA_PERSIST_DIRECTORY`, `CHROMA_COLLECTION_NAME`)
- Discord webhook URL
- Scheduling provider (Calendly or Google Calendar)
- Optional: LangSmith tracing variables (`LANGSMITH_*`)

### Conversation Memory

The agent uses LangChain's `ChatOpenAI` in stateless mode and layers a server-side
session store (`SessionMemory`) that persists recent chat messages per visitor.
Each request retrieves prior messages, appends the new user prompt, invokes the
model, and updates the history. Swap the in-memory store for Redis or another
shared cache in production to support multi-instance scaling.

## Deploying to AWS Lambda

The FastAPI application can run inside AWS Lambda by packaging it as a container image with [Mangum](https://github.com/jordaneremieff/mangum). Use the `Dockerfile.lambda` at the project root to build against the Python 3.10 Lambda base image:

```powershell
cd backend
./scripts/build_lambda_image.ps1 -ImageTag business-chatbot-backend:lambda
```

Provide `-RepositoryUri <aws_account_id>.dkr.ecr.<region>.amazonaws.com/business-chatbot-backend` to tag and push directly to ECR. Create the Lambda function with:

```powershell
aws lambda create-function `
  --function-name business-chatbot-backend `
  --package-type Image `
  --code ImageUri=<repo>/business-chatbot-backend:<tag> `
  --role arn:aws:iam::<account>:role/lambda-execution-role `
  --timeout 30 `
  --memory-size 2048
```

Subsequent updates only need `aws lambda update-function-code --function-name business-chatbot-backend --image-uri <repo>/<tag>`. Add an HTTP API Gateway proxy integration to expose the FastAPI routes, and configure the same environment variables you use locally (OpenAI keys, vector store paths, etc.).

## Deploying to Render (Free Tier)

This repository includes a `render.yaml` blueprint for spinning up the backend on Render's free Web Service plan.

1. Push the repository to GitHub (or GitLab/Bitbucket) so Render can access it.
2. In the Render dashboard choose **New -> Blueprint** and point it at the repo; `render.yaml` defines the service using `backend/` as `rootDir`.
3. Render will build with `pip install --upgrade pip && pip install .` and start via `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. The `/api/health` route is wired as the health check.
4. Supply environment variables such as `OPENAI_API_KEY`, `CHROMA_*`, and scheduling tokens in the Render UI. The blueprint pre-sets `ENVIRONMENT=production` and `DEBUG=0`.
5. Free Render services sleep after ~15 minutes without traffic; expect a short cold start when they wake. The container file system is ephemeral - persist long-lived state in Render Postgres or another external store if needed.
6. Pushes to the tracked branch trigger automatic redeploys. You can trigger manual rebuilds from the dashboard after rotating secrets or adjusting configuration.
