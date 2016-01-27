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
	@rm -rf function.zip deps/* template.json

function.zip: handler.py
	pip install -t deps boto3
	curl -s -o deps/cfn_resource.py https://raw.githubusercontent.com/ryansb/cfn-wrapper-python/master/cfn_resource.py
	cp handler.py deps
	cd deps && zip --quiet --recurse-paths ../function.zip *
