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
		--timeout-in-minutes 30 \
		--parameters '[{"ParameterKey": "Domains", "ParameterValue": "rsb.io,www.rsb.io"}]'

delete:
	aws cloudformation delete-stack --stack-name AcmRequestStack

function.zip: handler.py cfn_wrapper.py
	pip install -t deps boto3
	cp handler.py deps
	cp cfn_wrapper.py deps
	cd deps && zip -r ../function.zip *
