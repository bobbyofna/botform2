# AWS Security Group Configuration

## Server Details

- **Public IP**: 52.30.244.75
- **Server Port**: 8000
- **Server Status**: ✓ Running and listening on 0.0.0.0:8000

## Required Security Group Rules

To make the BotForm2 web interface accessible from the internet, you need to add the following inbound rule to your EC2 instance's security group:

### Inbound Rule

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | BotForm2 Web Interface |

**OR** for more security, restrict to your IP:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| Custom TCP | TCP | 8000 | YOUR_IP/32 | BotForm2 Web Interface |

## How to Add Security Group Rule

### Via AWS Console:

1. Go to EC2 Dashboard
2. Click on "Security Groups" in the left sidebar
3. Find and select your instance's security group
4. Click "Edit inbound rules"
5. Click "Add rule"
6. Configure:
   - Type: Custom TCP
   - Port range: 8000
   - Source: 0.0.0.0/0 (or your specific IP)
   - Description: BotForm2 Web Interface
7. Click "Save rules"

### Via AWS CLI:

```bash
# Get your security group ID first
aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text

# Add the rule (replace sg-xxxxxxxx with your security group ID)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

## Testing Access

Once the security group rule is added, test access with:

```bash
curl http://52.30.244.75:8000/health
```

Should return:
```json
{"status":"healthy","version":"1.0.0","environment":"development"}
```

## Web Interface URLs

After adding the security group rule, you can access:

- **Health Check**: http://52.30.244.75:8000/health
- **Homepage**: http://52.30.244.75:8000/
- **API Bots**: http://52.30.244.75:8000/api/bots

## Security Notes

- Consider restricting access to specific IP addresses instead of 0.0.0.0/0
- For production use, consider setting up:
  - HTTPS with a proper domain and SSL certificate
  - VPN access (already supported in the application via REQUIRE_VPN setting)
  - AWS Application Load Balancer with WAF rules
  - Rate limiting at the infrastructure level
