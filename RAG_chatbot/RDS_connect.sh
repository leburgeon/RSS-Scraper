# 1. Get the secret and extract only the password
export PGPASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id arn:aws:secretsmanager:eu-west-2:129033205317:secret:c22-rag-db-master-password-esbLiR \
  --region eu-west-2 \
  --query SecretString \
  --output text | jq -r .password)

# 2. Connect using the variable
psql -U media_group_project_RAG_DB \
     -h c22-media-rag-db.c57vkec7dkkx.eu-west-2.rds.amazonaws.com \
     -d rag_database