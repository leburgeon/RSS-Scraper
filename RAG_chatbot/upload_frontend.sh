aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 129033205317.dkr.ecr.eu-west-2.amazonaws.com

docker build -t c22-media-group-chatbot-frontend:latest .

docker tag c22-media-group-chatbot-frontend:latest 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c22-media-group-chatbot-frontend:latest

docker push 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c22-media-group-chatbot-frontend:latest