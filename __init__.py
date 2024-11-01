# -*- coding: utf-8 -*-

"""
This plugin opens the web console for a specific AWS service in the browser.
Trigger with 'aws '.
"""

import os
import json
from albert import *
from pathlib import Path

md_iid = '2.0'
md_version = "1.1"
md_name = "AWS services"
md_description = "Open AWS services in the browser"
md_license = "GPL-3.0"
md_url = "https://github.com/aironskin/albert-aws"
md_maintainers = "@aironskin"

AWS_REGION = "eu-west-1"
AWS_SERVICES_LIST = [
    # accounts
    { "name": "AWS Account: production", "url": "https://jobcloud-sso.awsapps.com/start/#/console?account_id=864261092842&role_name=AWSAdministratorAccess" },
    { "name": "AWS Account: playground", "url": "https://jobcloud-sso.awsapps.com/start/#/console?account_id=260677531019&role_name=AWSAdministratorAccess" },
    { "name": "AWS Account: torai", "url": "https://jobcloud-sso.awsapps.com/start/#/console?account_id=579888146138&role_name=AWSAdministratorAccess" },
    # management
    { "name": "AWS Account Portal", "url": "https://jobcloud-sso.awsapps.com/start#/" },
    { "name": "AWS Management Console", "url": "https://{0}.console.aws.amazon.com/console/home?region={0}".format(AWS_REGION) },
    { "name": "AWS Support Center", "url": "https://support.console.aws.amazon.com/support/home?region={0}#/case/history".format(AWS_REGION) },
    { "name": "AWS Cost Management", "url": "https://us-east-1.console.aws.amazon.com/cost-management/home#/dashboard" },
    { "name": "AWS Trusted Advisor", "url": "https://us-east-1.console.aws.amazon.com/trustedadvisor/home#/dashboard" },
    { "name": "AWS Systems Manager", "url": "https://{0}.console.aws.amazon.com/systems-manager/home?region={0}".format(AWS_REGION) },
    # identity management
    { "name": "AWS IAM Roles", "url": "https://us-east-1.console.aws.amazon.com/iamv2/home#/roles" },
    { "name": "AWS IAM Policies", "url": "https://us-east-1.console.aws.amazon.com/iamv2/home#/policies" },
    { "name": "AWS SSO", "url": "https://{0}.console.aws.amazon.com/singlesignon/identity/home?region={0}#!/".format(AWS_REGION) },
    # secrets management
    { "name": "AWS KMS", "url": "https://{0}.console.aws.amazon.com/kms/home?region={0}#/kms/keys".format(AWS_REGION) },
    { "name": "AWS SSM Parameter Store", "url": "https://{0}.console.aws.amazon.com/systems-manager/parameters/?region={0}&tab=Table".format(AWS_REGION) },
    { "name": "AWS Secrets Manager", "url": "https://{0}.console.aws.amazon.com/secretsmanager/listsecrets?region={0}".format(AWS_REGION) },
    # networking
    { "name": "AWS VPC", "url": "https://{0}.console.aws.amazon.com/vpc/home?region={0}#Home:".format(AWS_REGION) },
    # computing
    { "name": "AWS EC2", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#Home:".format(AWS_REGION) },
    { "name": "AWS EC2 Instances", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#Instances:v=3".format(AWS_REGION) },
    { "name": "AWS Elastic IPs", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#Addresses:".format(AWS_REGION) },
    { "name": "AWS Security Groups", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#SecurityGroups:".format(AWS_REGION) },
    { "name": "AWS Load Balancers", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#LoadBalancers:".format(AWS_REGION) },
    { "name": "AWS Target Groups", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#TargetGroups:".format(AWS_REGION) },
    # orchestration & automation
    { "name": "AWS ECR", "url": "https://{0}.console.aws.amazon.com/ecr/repositories?region={0}".format(AWS_REGION) },
    { "name": "AWS CloudFormation", "url": "https://{0}.console.aws.amazon.com/cloudformation/home?region={0}#/stacks".format(AWS_REGION) },
    { "name": "AWS ECS", "url": "https://{0}.console.aws.amazon.com/ecs/v2/clusters?region={0}".format(AWS_REGION) },
    { "name": "AWS Lambda", "url": "https://{0}.console.aws.amazon.com/lambda/home?region={0}#/functions".format(AWS_REGION) },
    { "name": "AWS Step Functions", "url": "https://{0}.console.aws.amazon.com/states/home?region={0}#/statemachines".format(AWS_REGION) },
    # file management
    { "name": "AWS S3", "url": "https://s3.console.aws.amazon.com/s3/buckets?region={0}".format(AWS_REGION) },
    { "name": "AWS EFS", "url": "https://{0}.console.aws.amazon.com/efs/home?region={0}#/file-systems".format(AWS_REGION) },
    { "name": "AWS Backup", "url": "https://{0}.console.aws.amazon.com/backup/home?region={0}#/dashboard".format(AWS_REGION) },
    # data management
    { "name": "AWS RDS", "url": "https://{0}.console.aws.amazon.com/rds/home?region={0}#databases:".format(AWS_REGION) },
    { "name": "AWS DocumentDB", "url": "https://{0}.console.aws.amazon.com/docdb/home?region={0}#dashboard".format(AWS_REGION) },
    { "name": "AWS DynamoDB", "url": "https://{0}.console.aws.amazon.com/dynamodbv2/home?region={0}#dashboard".format(AWS_REGION) },
    { "name": "AWS ElastiCache", "url": "https://{0}.console.aws.amazon.com/elasticache/home?region={0}#/dashboard".format(AWS_REGION) },
    { "name": "AWS SNS", "url": "https://{0}.console.aws.amazon.com/sns/v3/home?region={0}#/dashboard".format(AWS_REGION) },
    { "name": "AWS SQS", "url": "https://{0}.console.aws.amazon.com/sqs/v2/home?region={0}#/queues".format(AWS_REGION) },
    { "name": "AWS Redshift", "url": "https://{0}.console.aws.amazon.com/redshiftv2/home?region={0}#dashboard".format(AWS_REGION) },
    { "name": "AWS OpenSearch", "url": "https://{0}.console.aws.amazon.com/aos/home?region={0}#opensearch/domains".format(AWS_REGION) },
    # web resources
    { "name": "AWS ACM", "url": "https://{0}.console.aws.amazon.com/acm/home?region={0}#/certificates/list".format(AWS_REGION) },
    { "name": "AWS Route53 Hosted Zones", "url": "https://us-east-1.console.aws.amazon.com/route53/v2/hostedzones#" },
    { "name": "AWS Route53 Health Checks", "url": "https://us-east-1.console.aws.amazon.com/route53/healthchecks/home#/" },
    { "name": "AWS CloudFront", "url": "https://us-east-1.console.aws.amazon.com/cloudfront/v3/home#/distributions" },
    { "name": "AWS API Gateway", "url": "https://{0}.console.aws.amazon.com/apigateway/main/apis?region={0}".format(AWS_REGION) },
    { "name": "AWS Global Accelerator", "url": "https://us-west-2.console.aws.amazon.com/globalaccelerator/home#GlobalAcceleratorDashboard:" },
    { "name": "AWS WAF", "url": "https://us-east-1.console.aws.amazon.com/wafv2/homev2" },
    { "name": "AWS WAF WebACLs (regional)", "url": "https://us-east-1.console.aws.amazon.com/wafv2/homev2/web-acls?region={0}".format(AWS_REGION) },
    { "name": "AWS WAF WebACLs (global)", "url": "https://us-east-1.console.aws.amazon.com/wafv2/homev2/web-acls?region=global" },
    # user tools
    { "name": "AWS CloudShell", "url": "https://{0}.console.aws.amazon.com/cloudshell/home?region={0}#".format(AWS_REGION) },
    { "name": "AWS CodeBuild", "url": "https://{0}.console.aws.amazon.com/codesuite/codebuild/home?region={0}".format(AWS_REGION) },
    { "name": "AWS CodeDeploy", "url": "https://{0}.console.aws.amazon.com/codesuite/codedeploy/deployments?region={0}".format(AWS_REGION) },
    { "name": "AWS SSM Run Command", "url": "https://{0}.console.aws.amazon.com/systems-manager/run-command/executing-commands?region={0}".format(AWS_REGION) },
    # monitoring, alarming, events
    { "name": "AWS CloudWatch Alarms", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#alarmsV2:".format(AWS_REGION) },
    { "name": "AWS CloudWatch Log Groups", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#logsV2:log-groups".format(AWS_REGION) },
    { "name": "AWS CloudWatch Log Insights", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#logsV2:logs-insights".format(AWS_REGION) },
    { "name": "AWS CloudWatch Metrics", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#metricsV2:".format(AWS_REGION) },
    { "name": "AWS EventBridge Rules", "url": "https://{0}.console.aws.amazon.com/events/home?region={0}#/rules".format(AWS_REGION) },
    { "name": "AWS EventBridge Schedules", "url": "https://{0}.console.aws.amazon.com/scheduler/home?region={0}#schedules".format(AWS_REGION) },
    { "name": "AWS EventBridge Pipes", "url": "https://{0}.console.aws.amazon.com/events/home?region={0}#/pipes".format(AWS_REGION) },
    # documentation
    { "name": "AWS CLI v2 reference", "url": "https://awscli.amazonaws.com/v2/documentation/api/latest/index.html" }
]


class Plugin(PluginInstance, TriggerQueryHandler):

    def __init__(self):
        TriggerQueryHandler.__init__(self,
                                     id=md_id,
                                     name=md_name,
                                     description=md_description,
                                     defaultTrigger='aws ')
        PluginInstance.__init__(self, extensions=[self])
        self.iconUrls = [f"file:{Path(__file__).parent}/plugin.svg"]

    def load_services(self):
        return AWS_SERVICES_LIST

    def handleTriggerQuery(self, query):

        aws_services_list = self.load_services()

        query_stripped = query.string.strip().lower()

        if query_stripped:

            if not aws_services_list:
                return []

            results = []
            for service in aws_services_list:
                if query_stripped in service['name'].lower():
                    results.append(StandardItem(id=md_id,
                                                text=service["name"],
                                                iconUrls=self.iconUrls,
                                                subtext=service["url"],
                                                actions=[Action("open", "Open service URL", lambda u=service["url"]: openUrl(u))]))

            if results:
                query.add(results)
            else:
                query.add(StandardItem(id=md_id,
                                       text="No service matching search string",
                                       iconUrls=self.iconUrls))

        else:
            query.add(StandardItem(id=md_id,
                                   iconUrls=self.iconUrls,
                                   text="...",
                                   subtext="Search for an AWS service name"))
