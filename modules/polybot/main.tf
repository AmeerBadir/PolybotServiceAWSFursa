resource "aws_lb_target_group" "polybot-tg" {
  name     = "ameerb-target-g"
  port     = 8443
  protocol = "HTTPS"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/"
    port                = 8443
    protocol            = "HTTPS"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}
resource "aws_lb_target_group_attachment" "tf1-attachment-to-tg" {
  target_group_arn = aws_lb_target_group.polybot-tg.arn
  target_id        = aws_instance.tf_polybot1.id
  port             = 8443
}
resource "aws_lb_target_group_attachment" "tf2-attachment-to-tg" {
  target_group_arn = aws_lb_target_group.polybot-tg.arn
  target_id        = aws_instance.tf_polybot2.id
  port             = 8443
}


resource "aws_instance" "tf_polybot1" {
  ami           = var.ami_id
  instance_type = "t3.micro"
  key_name = var.key_name
  iam_instance_profile = var.role_name
  user_data = base64encode(templatefile("./modules/polybot/deploy.sh", {
    alb_dns_name   = aws_lb.polybot-lb.dns_name
    bucket_name    = var.bucket_name
    sqs_queue_url  = var.sqs_queue_url
    region_name = var.region_name
    dynamodb = var.dynamo_DB
  }))
  associate_public_ip_address = var.assign_public_ip
  security_groups = [aws_security_group.polybot-sg.id]

  subnet_id = var.public_subnets[0]
  tags = {
    Name = "ameerb-tf-polybot1"
  }
}

resource "aws_instance" "tf_polybot2" {
  ami           = var.ami_id
  instance_type = "t3.micro"
  key_name = var.key_name
  iam_instance_profile = var.role_name
  user_data = base64encode(templatefile("./modules/polybot/deploy.sh", {
    alb_dns_name   = aws_lb.polybot-lb.dns_name
    bucket_name    = var.bucket_name
    sqs_queue_url  = var.sqs_queue_url
    region_name = var.region_name
    dynamodb = var.dynamo_DB
  }))

  associate_public_ip_address = var.assign_public_ip
  security_groups = [aws_security_group.polybot-sg.id]
  subnet_id = var.public_subnets[1]
  tags = {
    Name = "ameerb-tf-polybot2"
  }
}



resource "aws_security_group" "polybot-sg" {
  name        = "ameer-polybot-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8443
    to_port     = 8443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


resource "aws_lb" "polybot-lb" {
  name               = "ameerb-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.polybot-sg.id]
  subnets            = var.public_subnets
}



resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.polybot-lb.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.polybot-tg.arn
  }
}

resource "aws_acm_certificate" "polybot_cert" {
  certificate_body       = file("./modules/polybot/YOURPUBLIC.pem")
  private_key            = file("./modules/polybot/YOURPRIVATE.key")

  tags = {
    Name = "Certifacte"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.polybot-lb.arn
  port              = "8443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.polybot_cert.arn


  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.polybot-tg.arn
  }
}


resource "aws_secretsmanager_secret" "bot_token" {
  name = "TELEGRAM_TOKEN"
}

resource "aws_secretsmanager_secret_version" "bot_token" {
  secret_id     = aws_secretsmanager_secret.bot_token.id
  secret_string = jsonencode({
    "TELEGRAM_TOKEN" = var.TF_VAR_botToken
  })
}




