# RSS Scraper & RAG Chatbot System

An end-to-end system that scrapes tech news from RSS feeds, performs NLP analysis, stores data in DynamoDB, and provides a conversational chatbot interface to query the data using RAG (Retrieval-Augmented Generation).

## Architecture Overview

```
RSS Feed → Extract → Transform (NLP/Sentiment) → Load (DynamoDB + RDS)
                                                        ↓
                                        Newsletter (HTML Report via Email)
                                                        ↓
                                        RAG Chatbot Embeddings (RDS)
                                                        ↓
                                        Streamlit UI + Lambda + API Gateway
```

## Prerequisites

- Python 3.13+
- AWS Account (for production deployment)
- Docker (for containerized deployment)
- Terraform (for AWS infrastructure)
- OpenAI API Key
- PostgreSQL connection (for RAG chatbot)

## Quick Start (Local Development)

### 1. Clone & Setup Environment

```bash
git clone <repo-url>
cd RSS-Scraper

# Create Python virtual environment
python3.13 -m venv .venv
source .venv/bin/activate
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with:

**RSS Pipeline:**
```
AWS_REGION=eu-west-2
TABLE_NAME=c22-rss-scraper-table
FEED_URL=<your-rss-feed-url>
OPENAI_API_KEY=<your-openai-key>
```

**RAG Chatbot (RDS Database):**
```
RDS_HOST=<database-endpoint>
RDS_PORT=5432
RDS_DB_NAME=rag_database
RDS_USER=<db-user>
RDS_PASSWORD=<db-password>
```

**Newsletter:**
```
AWS_REGION=eu-west-2
```

## Component Setup & Running

### RSS Pipeline (ETL)

Extracts articles from RSS feeds, performs NLP analysis (entity extraction, sentiment analysis), and stores data in DynamoDB and RDS.

**Setup:**
```bash
cd RSS_pipeline
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Run locally:**
```bash
python pipeline.py
```

**Run tests:**
```bash
pytest
```

**Docker deployment:**
```bash
docker build -t rss-scraper .
docker run --env-file .env rss-scraper
```

**AWS Scheduling:** Runs automatically via EventBridge (CloudWatch) scheduled task pushing Docker image to ECS Fargate.

---

### Newsletter Service

Generates HTML reports with metrics (mention volume, sentiment distribution, share of voice) and sends via email.

**Setup:**
```bash
cd Newsletter
pip install -r requirements.txt
```

**Run locally:**
```bash
python report.py
```

**Test metrics calculation:**
```bash
pytest
```

**AWS Deployment:** Lambda function triggered on schedule, pulls metrics from DynamoDB, sends email via SES.

**Build & push Docker image:**
```bash
./Newsletter_image_ecr_push.sh
```

---

### RAG Chatbot

Provides a Streamlit UI for querying news articles using OpenAI embeddings and vector similarity search.

**Setup:**
```bash
cd RAG_chatbot
pip install -r requirements.txt
```

**Run locally:**
```bash
streamlit run chatbot.py
```

**Architecture:** 
- **Frontend:** Streamlit UI (port 8501)
- **Backend:** AWS Lambda (performs RAG pipeline)
- **Database:** RDS PostgreSQL with vector embeddings
- **API:** API Gateway triggers Lambda on user queries

**Connect to RDS:**
```bash
./RDS_connect.sh
```

**Build & push Docker image:**
```bash
./docker-image-push.sh
```

---

## Database Setup

### DynamoDB (Articles & Entity Mentions)

Created automatically via Terraform. Stores:
- Article metadata (title, content, published date, source)
- Entity mentions with sentiment scores

### PostgreSQL RDS (RAG Database)

Created automatically via Terraform. Stores:
- Article chunks with OpenAI embeddings (for vector search)
- Entity names and publication dates

**Schema:** Automatically created by RAG_embedding.py when uploading articles.

---

## AWS Infrastructure Deployment

All infrastructure is managed via Terraform.

**Prerequisites:**
```bash
brew install terraform aws-cli
aws configure  # Set up AWS credentials
```

**Deploy:**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

**Resources created:**
- VPC & Security Groups
- DynamoDB table (c22-rss-scraper-table)
- RDS PostgreSQL instance
- ECS Fargate cluster for RSS pipeline
- Lambda functions (newsletter, chatbot)
- API Gateway (chatbot endpoint)
- ECR repositories (Docker images)
- CloudWatch logs

---

## Environment Variables Reference

| Variable | Component | Required | Description |
|----------|-----------|----------|-------------|
| `AWS_REGION` | All | Yes | AWS region (e.g., eu-west-2) |
| `TABLE_NAME` | RSS Pipeline | Yes | DynamoDB table name |
| `FEED_URL` | RSS Pipeline | Yes | RSS feed URL to scrape |
| `OPENAI_API_KEY` | All | Yes | OpenAI API key for embeddings |
| `RDS_HOST` | RAG Chatbot | Yes | RDS database endpoint |
| `RDS_PORT` | RAG Chatbot | Yes | RDS port (default: 5432) |
| `RDS_DB_NAME` | RAG Chatbot | Yes | Database name (rag_database) |
| `RDS_USER` | RAG Chatbot | Yes | Database user |
| `RDS_PASSWORD` | RAG Chatbot | Yes | Database password |

---

## Data Flow

1. **Extract:** RSS Pipeline polls feed URLs, extracts articles
2. **Filter:** Only new articles (since last run) are processed
3. **Transform:** NLP pipeline extracts entities, analyzes sentiment
4. **Load:** Articles stored in DynamoDB, chunks + embeddings in RDS
5. **Newsletter:** Report generator queries DynamoDB metrics, sends email
6. **RAG Chatbot:** User queries → Lambda embeds question → Vector search in RDS → LLM response

---

## Testing

Each component has unit tests:

```bash
# RSS Pipeline
cd RSS_pipeline && pytest

# Newsletter
cd Newsletter && pytest

# RAG Chatbot
# No automated tests; test via Streamlit UI
```

---

## Monitoring & Logs

CloudWatch logs are automatically created:
- **RSS Pipeline:** `/aws/ecs/c22-rss-scraper-cluster`
- **Newsletter Lambda:** `/aws/lambda/rss-report-lambda`
- **RAG Chatbot Lambda:** `/aws/lambda/rag-chatbot`

View logs:
```bash
aws logs tail /aws/ecs/c22-rss-scraper-cluster --follow
```

---

## Troubleshooting

**Articles not appearing in DynamoDB:**
- Check FEED_URL is correct and accessible
- Verify AWS credentials and IAM permissions
- Check CloudWatch logs for extraction errors

**RAG Chatbot slow responses:**
- Ensure RDS is running and accessible
- Check OpenAI API quotas
- Verify network connectivity via security groups

**Newsletter not sending:**
- Verify SES email addresses are verified in AWS
- Check Lambda execution role has SES permissions
- Review CloudWatch Lambda logs

**Spacy NLP issues:**
- Run `python -m spacy download en_core_web_sm` in RSS_pipeline venv
- Verify Python 3.13 is being used

---

## Project Structure

```
RSS-Scraper/
├── RSS_pipeline/          # ETL pipeline (extract, transform, load)
│   ├── pipeline.py        # Main orchestration script
│   ├── utils/             # NLP, data processing utilities
│   ├── RAG_embedding.py   # RDS upload with embeddings
│   └── testing/           # Unit tests
├── Newsletter/            # Report generation service
│   ├── report.py          # HTML report generator
│   ├── metrics.py         # DynamoDB metrics calculation
│   └── testing/           # Unit tests
├── RAG_chatbot/           # Streamlit frontend + Lambda backend
│   ├── chatbot.py         # Streamlit UI
│   ├── aws_lambda.py      # Lambda handler for RAG pipeline
│   └── RDS_connect.sh     # Database connection helper
└── terraform/             # AWS infrastructure as code
    ├── main.tf            # Provider, VPC, security
    ├── rss-pipeline-schedule.tf
    ├── newsletter_resources.tf
    └── RAG_chatbot.tf
```