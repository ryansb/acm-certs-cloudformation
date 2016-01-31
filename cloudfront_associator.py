# MIT Licensed, Copyright (c) 2015 Ryan Scott Brown <sb@ryansb.com>

import boto3
import logging
from botocore.exceptions import ClientError, ParamValidationError

import cfn_resource

log = logging.getLogger()
log.setLevel(logging.DEBUG)

cloudfront = boto3.client('cloudfront')
acm = boto3.client('acm')

def check_properties(event):
    properties = event['ResourceProperties']
    for p in ('CertificateArn', 'DistributionId'):
        if properties.get(p) is None:
            reason = "ERROR: No property '%s' on event %s" % (p, event)
            log.error(reason)
            return {
                'Status': 'FAILED',
                'Reason': reason,
                'PhysicalResourceId': 'could-not-create',
                'Data': {},
            }

    dist_id = properties['DistributionId']
    cert_arn = properties['CertificateArn']

    try:
        acm.get_certificate(CertificateArn=cert_arn)
    except ParamValidationError as e:
        log.exception('ARN for certificate not valid. Check CertificateArn property, got %s' % cert_arn)
        return {
            'Status': 'FAILED',
            'Reason': 'Bad CertificateArn, got %s' % cert_arn,
            'PhysicalResourceId': 'could-not-create',
            'Data': {},
        }
    except ClientError as e:
        code = e.response['ResponseMetadata']['HTTPStatusCode']
        if 400 <= code and code < 500:
            log.error('Distribution %s could not be found, got code %d' % (dist_id, code))
        log.exception('Failure getting cloudfront distribution')
        return {
            'Status': 'FAILED',
            'Reason': 'Failed to get CloudFront distribution, check DistributionId property',
            'PhysicalResourceId': 'could-not-create',
            'Data': {},
        }

    try:
        cloudfront.get_distribution(Id=dist_id)
    except ClientError as e:
        code = e.response['ResponseMetadata']['HTTPStatusCode']
        if 400 <= code and code < 500:
            log.error('Distribution %s could not be found' % dist_id)
        log.exception('Failure getting cloudfront distribution, got code %d' % code)
        return {
            'Status': 'FAILED',
            'Reason': 'Failed to get CloudFront distribution, check DistributionId property',
            'PhysicalResourceId': 'could-not-create',
            'Data': {},
        }


def generate_phys_id(cert_arn, dist_id):
    return "connection:%s:to:%s" % (cert_arn, dist_id)


def associate_cert(cert_arn, dist_id, config, etag):
    config['ViewerCertificate'] = {
        'Certificate': cert_arn,
        'CertificateSource': 'acm',
        'MinimumProtocolVersion': 'TLSv1',
        'SSLSupportMethod': 'sni-only'
    }
    return cloudfront.update_distribution(
        Id=dist_id,
        IfMatch=etag,
        DistributionConfig=config,
    )

handler = cfn_resource.Resource()


@handler.create
def create_cert_association(event, context):
    props = event['ResourceProperties']
    prop_errors = check_properties(event)
    if prop_errors:
        return prop_errors
    cert_arn = props['CertificateArn']
    dist_id = props['DistributionId']


    response = cloudfront.get_distribution_config(Id=dist_id)
    config = response['DistributionConfig']
    etag = response['ETag']

    reason = ''
    if config.get('ViewerCertificate') is None:
        return {
            'Status': 'FAILED',
            'Reason': 'No viewercert configuration',
            'Data': {}
        }
    elif config['ViewerCertificate'].get('CertificateSource', '') == 'acm':
        if config['ViewerCertificate']['Certificate'] == cert_arn:
            log.debug('Already configured - nothing to do')
            reason = 'Already connected, easy!'
        else:
            associate_cert(cert_arn, dist_id, config, etag)
            reason = 'Changed ACM cert ID'
    else:
        associate_cert(cert_arn, dist_id, config, etag)
        reason = 'Associated ACM cert'

    return {
        'Status': 'SUCCESS',
        'Reason': reason,
        'PhysicalResourceId': generate_phys_id(cert_arn, dist_id),
        'Data': {},
    }


@handler.update
def update_certificate(event, context):
    return create_cert_association(event, context)


@handler.delete
def dissociate_cert(event, context):
    return {
        'Status': 'SUCCESS',
        'Reason': 'Dissociating is not supported because the distribution will likely be deleted after this',
        'PhysicalResourceId': event['PhysicalResourceId'],
        'Data': {},
    }
