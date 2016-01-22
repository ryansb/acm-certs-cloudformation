# MIT Licensed, Copyright (c) 2015 Ryan Scott Brown <sb@ryansb.com>

import json
import logging
import urllib2

logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""
Event example
{
    "Status": SUCCESS | FAILED,
    "Reason: mandatory on failure
    "PhysicalResourceId": string,
    "StackId": event["StackId"],
    "RequestId": event["RequestId"],
    "LogicalResourceId": event["LogicalResourceId"],
    "Data": {}
}
"""

def cfn_resource(func):
    def wrapper_func(event, context):
        response = {
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"],
            "Status": "SUCCESS",
        }

        logger.debug("Received %s request with event: %s" % (event['RequestType'], json.dumps(event)))

        try:
            response.update(func(event, context))
        except:
            logger.exception("Failed to execute resource function")
            response.update({
                "Status": "FAILED",
                "Reason": "Exception was raised while handling custom resource"
            })

        serialized = json.dumps(response)
        logger.info("Responding to '%s' request with: %s" % (
            event['RequestType'], serialized))

        req = urllib2.Request(
            event['ResponseURL'], data=serialized,
            headers={'Content-Length': len(serialized),
                     'Content-Type': ''}
        )
        req.get_method = lambda: 'PUT'

        try:
            urllib2.urlopen(req)
            logger.debug("Request to CFN API succeeded, nothing to do here")
        except urllib2.HTTPError as e:
            logger.error("Callback to CFN API failed with status %d" % e.code)
            logger.error("Response: %s" % e.reason)
        except urllib2.URLError as e:
            logger.error("Failed to reach the server - %s" % e.reason)

    return wrapper_func
