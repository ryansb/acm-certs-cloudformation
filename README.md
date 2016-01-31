# Custom Resource to support AWS Certificate Manager

This is a pair of resources to support adding the new [ACM][acm] SSL
certificates automatically in CloudFormation. Right now, it creates a
certificate request given a comma-separated list of domains. The second
resource adds support for configuring the cert on a CloudFront distribution.

Sample usage:

```
"ProdAcmCertificate": {
    "Type": "Custom::AcmCertificateRequest",
    "Properties": {
        "Domains": ["mysite.com", "*.mysite.com"],
        "ServiceToken": "ARN of your instance of the Lambda function in this repo"
    }
}
```

For a full example, see the `template.json` file in this repository. It creates
a CloudFront distribution and issues an ACM certificate, and associates that
cert with the distribution.

Todo:
- [x] Create a CertRequest
- [x] Delete CertRequest on resource delete
- [x] Sample CloudFormation template
- [x] Wait for the cert to be issued
- [ ] provide a boolean attribute for whether the cert is issued
- [x] provide cert ID for CloudFront/ELB
- [x] Handle updates?

[acm]: https://aws.amazon.com/blogs/aws/new-aws-certificate-manager-deploy-ssltls-based-apps-on-aws/
