all:
	@echo "Use 'make create_iam' and 'update_iam' to deploy the CloudFormation stack with execution roles"
	@echo "Use 'make create' to deploy the CloudFormation demo stack with your domains"
	@echo "Use 'make delete' to delete the CloudFormation stack"

create_iam:
	aws cloudformation create-stack --stack-name AcmResourceRoles \
		--template-body file://iam_role.json

update_iam:
	aws cloudformation update-stack --stack-name AcmResourceRoles \
		--template-body file://iam_role.json

delete_iam:
	aws cloudformation delete-stack --stack-name AcmResourceRoles \
		--template-body file://iam_role.json

create:
	aws cloudformation create-stack --stack-name AcmRequestStack \
		--template-body file://template.json \
		--timeout-in-minutes 15 \
		--parameters '[{"ParameterKey": "Domains", "ParameterValue": "ryansb.com,www.ryansb.com"}]'

update:
	aws cloudformation create-stack --stack-name AcmRequestStack \
		--template-body file://template.json \
		--timeout-in-minutes 15 \
		--parameters '[{"ParameterKey": "Domains", "ParameterValue": "ryansb.com,www.ryansb.com"}]'

delete:
	aws cloudformation delete-stack --stack-name AcmRequestStack

clean:
	@rm -rf acm-functions.zip deps/* template.json

acm-functions.zip: acm_handler.py cloudfront_associator.py
	pip install -t deps boto3 cfn_resource
	cp *.py deps/
	cd deps && zip --quiet --recurse-paths ../acm-functions.zip *
