"""
Error handling of the forensic Lambdas. Throttling and other transient AWS errors leave them as
AWSTransientError, which the state machine retries before its catch raises the alert. The polling
RuntimeError ("snapshot not finished yet", "incron not ready yet") keeps its name and its own retry rule.

A retry re-runs the whole Lambda, so a Lambda that changes something before a later call can be throttled
must cope with having run before: MountVolume does not attach a volume that is already attached.
"""

from unittest.mock import MagicMock, patch

import botocore.exceptions
import pytest

from aws_errors import AWSTransientError
from functions.CheckSnapshot import lambda_function as check_snapshot
from functions.MountVolume import lambda_function as mount_volume
from functions.TerminateInstance import lambda_function as terminate_instance


def client_error(code, status=400):
    return botocore.exceptions.ClientError(
        {'Error': {'Code': code, 'Message': code}, 'ResponseMetadata': {'HTTPStatusCode': status}}, 'op')


THROTTLE = client_error('RequestLimitExceeded', 503)


def clients(**by_service):
    """boto3.client replacement returning the given mock per service (a fresh MagicMock otherwise)."""
    return lambda service, *args, **kwargs: by_service.get(service, MagicMock(name=service))


# ---------------------------------------------------------------------------
# MountVolume
# ---------------------------------------------------------------------------

DISK = {'DiskProcess': {'ForensicInstances': ['i-forensic'], 'ForensicVolumeID': 'vol-1',
                        'EvidenceBucket': 'example-evidence', 'IncidentID': 'incident-1',
                        'SourceVolumeID': 'vol-source'}}


def mount(ec2, s3=None, incron='incron is running'):
    logs = MagicMock()
    logs.get_log_events.return_value = {'events': [{'message': incron}]}
    logs.describe_log_streams.return_value = {'logStreams': [{}]}
    with patch.object(mount_volume.boto3, 'client', side_effect=clients(ec2=ec2, logs=logs, s3=s3 or MagicMock())):
        return mount_volume.lambda_handler(DISK, None)


def volume(attached_to=None):
    ec2 = MagicMock()
    attachments = [{'InstanceId': attached_to, 'State': 'attached'}] if attached_to else []
    ec2.describe_volumes.return_value = {'Volumes': [{'VolumeId': 'vol-1', 'Attachments': attachments}]}
    return ec2


def test_mounts_the_volume():
    ec2 = volume()
    mount(ec2)
    ec2.attach_volume.assert_called_once_with(Device='/dev/sdf', InstanceId='i-forensic', VolumeId='vol-1')


def test_a_retry_after_a_throttle_later_on_does_not_attach_the_volume_again():
    s3 = MagicMock()
    s3.put_object.side_effect = THROTTLE
    with pytest.raises(AWSTransientError):
        mount(volume(), s3=s3)
    ec2 = volume(attached_to='i-forensic')  # the attach of the first run succeeded
    mount(ec2)
    ec2.attach_volume.assert_not_called()


def test_a_volume_attached_elsewhere_is_still_attached_here_and_fails_as_before():
    ec2 = volume(attached_to='i-other')
    ec2.attach_volume.side_effect = client_error('VolumeInUse')
    with pytest.raises(botocore.exceptions.ClientError) as raised:
        mount(ec2)
    assert not isinstance(raised.value, AWSTransientError)


def test_a_throttled_attach_is_retried():
    ec2 = volume()
    ec2.attach_volume.side_effect = THROTTLE
    with pytest.raises(AWSTransientError):
        mount(ec2)


def test_waiting_for_incron_keeps_its_polling_error():
    with pytest.raises(RuntimeError) as raised:
        mount(volume(), incron='starting')
    assert type(raised.value) is RuntimeError


# ---------------------------------------------------------------------------
# CheckSnapshot
# ---------------------------------------------------------------------------

SNAPSHOTS = {'DiskProcess': {'Resource': {'Id': 'i-rogue', 'Region': 'eu-north-1'}, 'FindingId': 'finding-1',
                             'AwsAccountId': '222222222222', 'CapturedSnapshots': [{'SourceSnapshotID': 'snap-1'}],
                             'EvidenceBucket': 'example-evidence', 'IncidentID': 'incident-1'}}


def check(ec2):
    session = MagicMock()
    session.client.return_value = ec2
    with patch.object(check_snapshot.boto3, 'Session', return_value=session):
        return check_snapshot.lambda_handler(SNAPSHOTS, None)


def test_a_pending_snapshot_keeps_its_polling_error():
    ec2 = MagicMock()
    ec2.describe_snapshots.return_value = {'Snapshots': [{'SnapshotId': 'snap-1', 'State': 'pending'}]}
    with pytest.raises(RuntimeError) as raised:
        check(ec2)
    assert type(raised.value) is RuntimeError


def test_a_throttled_snapshot_check_is_retried():
    ec2 = MagicMock()
    ec2.describe_snapshots.side_effect = THROTTLE
    with pytest.raises(AWSTransientError):
        check(ec2)


# ---------------------------------------------------------------------------
# TerminateInstance
# ---------------------------------------------------------------------------

ROGUE = {'Terminate': 'Yes', 'Region': 'eu-north-1', 'AwsAccountId': '222222222222',
         'InstanceARN': 'arn:aws:ec2:eu-north-1:222222222222:instance/i-rogue'}


def terminate(ec2):
    sts = MagicMock()
    sts.assume_role.return_value = {'Credentials': {'AccessKeyId': 'a', 'SecretAccessKey': 'b',
                                                    'SessionToken': 'c'}}
    with patch.object(terminate_instance, 'sts_client', sts), \
            patch.object(terminate_instance.boto3, 'client', return_value=ec2):
        return terminate_instance.lambda_handler(dict(ROGUE), None)


def test_terminates_the_instance():
    ec2 = MagicMock()
    assert terminate(ec2) is True
    ec2.terminate_instances.assert_called_once_with(InstanceIds=['i-rogue'])


def test_a_throttled_protection_removal_is_retried_not_skipped():
    ec2 = MagicMock()
    ec2.modify_instance_attribute.side_effect = THROTTLE
    with pytest.raises(AWSTransientError):
        terminate(ec2)
    ec2.terminate_instances.assert_not_called()


def test_a_refused_protection_removal_is_still_skipped():
    ec2 = MagicMock()
    ec2.modify_instance_attribute.side_effect = client_error('UnauthorizedOperation', 403)
    assert terminate(ec2) is True
    ec2.terminate_instances.assert_called_once()


def test_a_throttled_termination_is_retried():
    ec2 = MagicMock()
    ec2.terminate_instances.side_effect = THROTTLE
    with pytest.raises(AWSTransientError):
        terminate(ec2)
