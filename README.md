# Custom Resource to support AWS Certificate Manager

This is a (beta) resource to support adding the new [ACM][acm] SSL certificates
automatically in CloudFormation. Right now, it creates a certificate request
given a comma-separated list of domains. You still need to add it to the
CloudFront or ELB you use, and click through the confirmation email.

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

Todo:
- [x] Create a CertRequest
- [x] Delete CertRequest on resource delete
- [x] Sample CloudFormation template
- [ ] provide a boolean attribute for whether the cert is issued
- [ ] provide cert ID for CloudFront/ELB
- [ ] Handle updates?

[acm]: https://aws.amazon.com/blogs/aws/new-aws-certificate-manager-deploy-ssltls-based-apps-on-aws/
