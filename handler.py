# MIT Licensed, Copyright (c) 2015 Ryan Scott Brown <sb@ryansb.com>

import boto3
import hashlib
import logging
import time
from botocore.exceptions import ClientError

import cfn_resource

log = logging.getLogger()
log.setLevel(logging.DEBUG)

acm = boto3.client('acm')

def await_validation(domain, context):
    # as long as we have at least 10 seconds left
    while context.get_remaining_time_in_millis() > 10000:
        time.sleep(5)
        resp = acm.list_certificates(CertificateStatuses=['ISSUED'])
        if any(cert['DomainName'] == domain for cert in resp['CertificateSummaryList']):
            cert_info = [cert for cert in resp['CertificateSummaryList']
                         if cert['DomainName'] == domain][0]
            log.info("Certificate has been issued for domain %s, ARN: %s" %
                     (domain, cert_info['CertificateArn']))
            return cert_info['CertificateArn']
        log.info("Awaiting cert for domain %s" % domain)

    log.warning("Timed out waiting for cert for domain %s" % domain)

def check_properties(event):
    properties = event['ResourceProperties']
    for p in ('Domains', ):
        if properties.get(p) is None:
            reason = "ERROR: No property '%s' on event %s" % (p, event)
            log.error(reason)
            return {
                'Status': 'FAILED',
                'Reason': reason,
                'PhysicalResourceId': 'could-not-create',
                'Data': {},
            }

    dom = properties.get('Domains', list)
    log.info("Got domains %s" % dom)

    if not (isinstance(dom, list) and len(dom) >= 1):
        reason = "ERROR: Domains is not a list in event %s" % event
        log.error(reason)
        return {
            'Status': 'FAILED',
            'Reason': reason,
            'PhysicalResourceId': 'could-not-create',
            'Data': {},
        }


handler = cfn_resource.Resource()


@handler.create
def create_cert(event, context):
    props = event['ResourceProperties']
    prop_errors = check_properties(event)
    if prop_errors:
        return prop_errors
    domains = props['Domains']

    # take a hash of the Stack & resource ID to make a request token
    id_token = hashlib.md5('cfn-{StackId}-{LogicalResourceId}'.format(
        **event)).hexdigest()
    kwargs = {
        'DomainName': domains[0],
        # the idempotency token length limit is 31 characters
        'IdempotencyToken': id_token[:30]
    }

    if len(domains) > 1:
        # add alternative names if the user wants more names
        # wildcards are allowed
        kwargs['SubjectAlternativeNames'] = domains[1:]

    if props.get('ValidationOptions'):
        # TODO validate format of this parameter
        """ List of domain validation options. Looks like:
        {
            "DomainName": "test.foo.com",
            "ValidationDomain": "foo.com",
        }
        """
        kwargs['DomainValidationOptions'] = props.get('ValidationOptions')

    response = acm.request_certificate(**kwargs)
    if props.get('Await', False):
        await_validation(domains[0], context)

    return {
        'Status': 'SUCCESS',
        'Reason': 'Cert request created successfully',
        'PhysicalResourceId': response['CertificateArn'],
        'Data': {},
    }


@handler.update
def update_certificate(event, context):
    props = event['ResourceProperties']
    prop_errors = check_properties(event)
    if prop_errors:
        return prop_errors
    domains = props['Domains']
    arn = event['PhysicalResourceId']
    if not arn.startswith('arn:aws:acm:'):
        return create_cert(event, context)

    try:
        cert = acm.describe_certificate(CertificateArn=arn)
    except ClientError:
        # cert doesn't exist! make it
        return create_cert(event, context)

    if cert['Certificate']['Status'] == 'PENDING_VALIDATION' and props.get('Await', False):
        # cert isn't yet valid, wait as long as we can until it is
        await_validation(domains[0], context)

    if sorted(domains) != sorted(cert['Certificate']['SubjectAlternativeNames']):
        # domain names have changed, need to delete & rebuild
        try:
            acm.delete_certificate(CertificateArn=event['PhysicalResourceId'])
        except:
            log.exception('Failure deleting cert with arn %s' % event['PhysicalResourceId'])
        return create_cert(event, context)

    return {'Status': 'SUCCESS',
            'Reason': 'Nothing to do, we think',
            'Data': {}
            }


@handler.delete
def delete_certificate(event, context):
    resp = {'Status': 'SUCCESS',
            'PhysicalResourceId': event['PhysicalResourceId'],
            'Data': {},
            }
    try:
        acm.delete_certificate(CertificateArn=event['PhysicalResourceId'])
    except:
        log.exception('Failure deleting cert with arn %s' % event['PhysicalResourceId'])
        resp['Reason'] = 'Some exception was raised while deleting the cert'
    return resp
