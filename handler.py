# MIT Licensed, Copyright (c) 2015 Ryan Scott Brown <sb@ryansb.com>

import boto3
import hashlib
import json
import logging

from cfn_wrapper import cfn_resource

log = logging.getLogger()
log.setLevel(logging.DEBUG)

acm = boto3.client('acm')

def check_properties(event):
    if event['RequestType'] == 'Delete':
        # don't validate on delete
        return

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

@cfn_resource
def handler(event, context):
    log.debug("Received event {}".format(json.dumps(event)))
    props = event['ResourceProperties']
    prop_errors = check_properties(event)
    if prop_errors:
        return prop_errors

    domains = props['Domains']

    if event['RequestType'] == 'Delete':
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

    if event['RequestType'] == 'Update':
        return {
            'Status': 'SUCCESS',
            'PhysicalResourceId': event['PhysicalResourceId'],
            'Reason': 'Life is good, man',
            'Data': {},
        }

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

    if props.get('ValidationDomain'):
        kwargs['DomainValidationOptions'] = {
            'DomainName': domains[0],
            'ValidationDomain': props['ValidationDomain'],
        }

    response = acm.request_certificate(**kwargs)

    return {
        'Status': 'SUCCESS',
        'Reason': 'Cert request created successfully',
        'PhysicalResourceId': response['CertificateArn'],
        'Data': {},
    }
