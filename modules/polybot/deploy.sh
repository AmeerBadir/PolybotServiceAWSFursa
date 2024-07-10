#!/bin/bash
apt-get update
apt-get install ca-certificates curl -y
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update

# Install docker
apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

usermod -aG docker ubuntu

docker run -d -p 8443:8443 --name polybot3 --restart always -e TELEGRAM_APP_URL=https://dev-tel.ameer-domain.click:8443 -e BUCKET_NAME="${bucket_name}" -e REGION="${region_name}" -e SQS_QUEUE="${sqs_queue_url}" -e DB_TABLE_NAME="${dynamodb}" ameerbadir/ameerb_tf_poly:0.0.1
