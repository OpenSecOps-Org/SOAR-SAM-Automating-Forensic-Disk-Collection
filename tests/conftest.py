import os
import sys
from unittest.mock import MagicMock, patch

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
# The Lambdas import aws_errors from their layer, as they do in AWS
sys.path.insert(0, os.path.join(ROOT, 'functions', 'layers', 'aws_errors', 'python'))

# Module-level boto3 clients are created at import; no call is made, but a region is needed
os.environ.setdefault('AWS_DEFAULT_REGION', 'eu-north-1')
for name, value in {'AMI_IDS': 'eu-north-1:ami-00000000', 'EVIDENCE_BUCKET': 'example-evidence',
                    'ForensicSFNARN': 'arn:aws:states:eu-north-1:111111111111:stateMachine:example',
                    'INSTANCE_PROFILE_NAME': 'example-profile', 'INSTANCE_TYPE': 'm5.large',
                    'KMS_KEY': 'arn:aws:kms:eu-north-1:111111111111:key/example', 'LOG_GROUP': 'example-log-group',
                    'REGION': 'eu-north-1', 'ROLE_NAME': 'example-role', 'SECURITY_ACCOUNT': '111111111111',
                    'SECURITY_GROUP': 'sg-00000000', 'SUPPORTED_AZS': 'eu-north-1a', 'VPC_ID': 'vpc-00000000'}.items():
    os.environ.setdefault(name, value)


@pytest.fixture(autouse=True)
def mock_aws_services():
    """Prevents ALL AWS API calls: every boto3 client and session the Lambdas create is a MagicMock."""
    with patch('boto3.client', side_effect=lambda *args, **kwargs: MagicMock(name=f'client:{args[0]}')), \
            patch('boto3.Session', side_effect=lambda *args, **kwargs: MagicMock(name='session')):
        yield
