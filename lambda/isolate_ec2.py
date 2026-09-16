"""
isolate_ec2.py
----------------
AWS Lambda function that isolates an EC2 instance by swapping its
security group to a pre-created "quarantine" group (isolation-sg)
with zero inbound/outbound rules.

Triggered via a Lambda Function URL, called directly from the
Shuffle SOAR workflow as the automated containment step once a
suspicious IP crosses the AbuseIPDB confidence-score threshold.

IMPORTANT — Function URL body handling:
AWS wraps the raw POST body as a STRING inside event['body'],
it does NOT merge the JSON keys directly into the event dict.
This tripped up the first version of this function (see
../docs/TROUBLESHOOTING.md, issue #4) — always json.loads()
event['body'] before reading fields out of it.
"""

import boto3
import json

# Security group with no inbound/outbound rules — see aws-setup/README.md
# for why this approach was chosen over other isolation methods.
ISOLATION_SECURITY_GROUP_ID = "sg-07f3a0cd92fe8d885"
REGION = "us-east-1"


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        body = {}

    instance_id = body.get("instance_id")

    if not instance_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "instance_id is required"}),
        }

    ec2 = boto3.client("ec2", region_name=REGION)
    ec2.modify_instance_attribute(
        InstanceId=instance_id,
        Groups=[ISOLATION_SECURITY_GROUP_ID],
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": f"Instance {instance_id} isolated successfully."}
        ),
    }
