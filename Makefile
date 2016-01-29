all:
	@echo "Use 'make master.json' to generate the CloudFormation template without uploading"
	@echo "Use 'make create' to deploy the CloudFormation stack"
	@echo "Use 'make update' to re-deploy the CloudFormation stack"
	@echo "Use 'make delete' to delete the CloudFormation stack"

template.json: template.yml
	@python ./minify.py < template.yml > template.json
	@sed -i -e 's/ $$//' template.json
	@echo "Generated master CFN template"

create: template.json
	aws cloudformation create-stack --stack-name AcmRequestStack \
		--template-body file://template.json \
		--timeout-in-minutes 15 \
		--parameters '[{"ParameterKey": "Domains", "ParameterValue": "rsb.io,www.rsb.io"}]'

update: template.json
	aws cloudformation update-stack --stack-name AcmRequestStack \
		--template-body file://template.json \
		--parameters '[{"ParameterKey": "Domains", "ParameterValue": "rsb.io,www.rsb.io"}]'

delete:
	aws cloudformation delete-stack --stack-name AcmRequestStack

clean:
	@rm -rf acm-function.zip assoc-function.zip deps/* template.json

acm-function.zip: acm_handler.py
	pip install -t deps boto3 cfn_resource
	curl -s -o deps/cfn_resource.py https://raw.githubusercontent.com/ryansb/cfn-wrapper-python/master/cfn_resource.py
	cp acm_handler.py deps/handler.py
	cd deps && zip --quiet --recurse-paths ../acm-function.zip *

assoc-function.zip: cloudfront_associator.py
	pip install -t deps boto3 cfn_resource
	cp cloudfront_associator.py deps/handler.py
	cd deps && zip --quiet --recurse-paths ../assoc-function.zip *

upload: acm-function.zip assoc-function.zip
	aws s3 cp --acl public-read assoc-function.zip s3://demos.serverlesscode.com/acm-certificate-function.zip
	aws s3 cp --acl public-read acm-function.zip s3://demos.serverlesscode.com/acm-associate-certificate-function.zip
