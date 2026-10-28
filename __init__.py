# -*- coding: utf-8 -*-

"""
This plugin opens the web console for a specific AWS service in the browser.
Trigger with 'aws '.
"""

from albert import Action, GeneratorQueryHandler, Icon, PluginInstance, StandardItem, openUrl
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit
import json
import re

md_iid = "5.0"
md_version = "2.0"
md_name = "AWS services"
md_description = "Open AWS services in the browser"
md_license = "GPL-3.0"
md_url = "https://github.com/aironskin/albert-aws"
md_authors = ["@aironskin"]

DEFAULT_AWS_REGION = "eu-west-1"
AWS_URL_LIST = [
    # management
    { "name": "AWS Management Console", "url": "https://{0}.console.aws.amazon.com/console/home?region={0}" },
    { "name": "AWS Support Center", "url": "https://support.console.aws.amazon.com/support/home?region={0}#/case/history" },
    { "name": "AWS Cost Management", "url": "https://us-east-1.console.aws.amazon.com/cost-management/home#/dashboard" },
    { "name": "AWS Trusted Advisor", "url": "https://us-east-1.console.aws.amazon.com/trustedadvisor/home#/dashboard" },
    { "name": "AWS Systems Manager", "url": "https://{0}.console.aws.amazon.com/systems-manager/home?region={0}" },
    # identity management
    { "name": "AWS IAM Roles", "url": "https://us-east-1.console.aws.amazon.com/iamv2/home#/roles" },
    { "name": "AWS IAM Policies", "url": "https://us-east-1.console.aws.amazon.com/iamv2/home#/policies" },
    { "name": "AWS SSO", "url": "https://{0}.console.aws.amazon.com/singlesignon/identity/home?region={0}#!/" },
    # secrets management
    { "name": "AWS KMS", "url": "https://{0}.console.aws.amazon.com/kms/home?region={0}#/kms/keys" },
    { "name": "AWS SSM Parameter Store", "url": "https://{0}.console.aws.amazon.com/systems-manager/parameters/?region={0}&tab=Table" },
    { "name": "AWS Secrets Manager", "url": "https://{0}.console.aws.amazon.com/secretsmanager/listsecrets?region={0}" },
    # networking
    { "name": "AWS VPC", "url": "https://{0}.console.aws.amazon.com/vpc/home?region={0}#Home:" },
    { "name": "AWS VPC Endpoints", "url": "https://{0}.console.aws.amazon.com/vpc/home?region={0}#Endpoints:" },
    { "name": "AWS Transit Gateway", "url": "https://{0}.console.aws.amazon.com/vpc/home?region={0}#TransitGateways:" },
    { "name": "AWS VPC Peering", "url": "https://{0}.console.aws.amazon.com/vpc/home?region={0}#PeeringConnections:" },
    # computing
    { "name": "AWS EC2", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#Home:" },
    { "name": "AWS EC2 Instances", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#Instances:v=3" },
    { "name": "AWS EC2 Auto Scaling Groups", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#AutoScalingGroups:" },
    { "name": "AWS EC2 Launch Templates", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#LaunchTemplates:" },
    { "name": "AWS Batch", "url": "https://{0}.console.aws.amazon.com/batch/home?region={0}#dashboard" },
    { "name": "AWS Elastic IPs", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#Addresses:" },
    { "name": "AWS Security Groups", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#SecurityGroups:" },
    { "name": "AWS Load Balancers", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#LoadBalancers:" },
    { "name": "AWS Target Groups", "url": "https://{0}.console.aws.amazon.com/ec2/home?region={0}#TargetGroups:" },
    # orchestration & automation
    { "name": "AWS ECR", "url": "https://{0}.console.aws.amazon.com/ecr/repositories?region={0}" },
    { "name": "AWS CloudFormation", "url": "https://{0}.console.aws.amazon.com/cloudformation/home?region={0}#/stacks" },
    { "name": "AWS ECS", "url": "https://{0}.console.aws.amazon.com/ecs/v2/clusters?region={0}" },
    { "name": "AWS Lambda", "url": "https://{0}.console.aws.amazon.com/lambda/home?region={0}#/functions" },
    { "name": "AWS Step Functions", "url": "https://{0}.console.aws.amazon.com/states/home?region={0}#/statemachines" },
    { "name": "AWS CloudMap", "url": "https://{0}.console.aws.amazon.com/cloudmap/home/namespaces?region={0}" },
    # file management
    { "name": "AWS S3", "url": "https://s3.console.aws.amazon.com/s3/buckets?region={0}" },
    { "name": "AWS EFS", "url": "https://{0}.console.aws.amazon.com/efs/home?region={0}#/file-systems" },
    { "name": "AWS Backup", "url": "https://{0}.console.aws.amazon.com/backup/home?region={0}#/dashboard" },
    # data management
    { "name": "AWS RDS", "url": "https://{0}.console.aws.amazon.com/rds/home?region={0}#databases:" },
    { "name": "AWS DocumentDB", "url": "https://{0}.console.aws.amazon.com/docdb/home?region={0}#dashboard" },
    { "name": "AWS DynamoDB", "url": "https://{0}.console.aws.amazon.com/dynamodbv2/home?region={0}#dashboard" },
    { "name": "AWS ElastiCache", "url": "https://{0}.console.aws.amazon.com/elasticache/home?region={0}#/dashboard" },
    { "name": "AWS ElastiCache Valkey", "url": "https://{0}.console.aws.amazon.com/elasticache/home?region={0}#/valkey" },
    { "name": "AWS SNS", "url": "https://{0}.console.aws.amazon.com/sns/v3/home?region={0}#/dashboard" },
    { "name": "AWS SQS", "url": "https://{0}.console.aws.amazon.com/sqs/v2/home?region={0}#/queues" },
    { "name": "AWS Redshift", "url": "https://{0}.console.aws.amazon.com/redshiftv2/home?region={0}#dashboard" },
    { "name": "AWS OpenSearch", "url": "https://{0}.console.aws.amazon.com/aos/home?region={0}#opensearch/domains" },
    { "name": "AWS OpenSearch Serverless", "url": "https://{0}.console.aws.amazon.com/aos/home?region={0}#opensearch/collections" },
    # analytics
    { "name": "AWS Athena", "url": "https://{0}.console.aws.amazon.com/athena/home?region={0}" },
    { "name": "AWS Glue", "url": "https://{0}.console.aws.amazon.com/glue/home?region={0}" },
    # artificial intelligence
    { "name": "AWS Bedrock", "url": "https://{0}.console.aws.amazon.com/bedrock/home?region={0}" },
    # web resources
    { "name": "AWS ACM", "url": "https://{0}.console.aws.amazon.com/acm/home?region={0}#/certificates/list" },
    { "name": "AWS Route53 Hosted Zones", "url": "https://us-east-1.console.aws.amazon.com/route53/v2/hostedzones#" },
    { "name": "AWS Route53 Health Checks", "url": "https://us-east-1.console.aws.amazon.com/route53/healthchecks/home#/" },
    { "name": "AWS CloudFront", "url": "https://us-east-1.console.aws.amazon.com/cloudfront/v3/home#/distributions" },
    { "name": "AWS API Gateway", "url": "https://{0}.console.aws.amazon.com/apigateway/main/apis?region={0}" },
    { "name": "AWS Global Accelerator", "url": "https://us-west-2.console.aws.amazon.com/globalaccelerator/home#GlobalAcceleratorDashboard:" },
    { "name": "AWS WAF", "url": "https://us-east-1.console.aws.amazon.com/wafv2/homev2" },
    { "name": "AWS WAF WebACLs (regional)", "url": "https://us-east-1.console.aws.amazon.com/wafv2/homev2/web-acls?region={0}" },
    { "name": "AWS WAF WebACLs (global)", "url": "https://us-east-1.console.aws.amazon.com/wafv2/homev2/web-acls?region=global" },
    # user tools
    { "name": "AWS SES", "url": "https://{0}.console.aws.amazon.com/ses/home?region={0}" },
    { "name": "AWS CloudShell", "url": "https://{0}.console.aws.amazon.com/cloudshell/home?region={0}#" },
    { "name": "AWS CodeBuild", "url": "https://{0}.console.aws.amazon.com/codesuite/codebuild/home?region={0}" },
    { "name": "AWS CodeDeploy", "url": "https://{0}.console.aws.amazon.com/codesuite/codedeploy/deployments?region={0}" },
    { "name": "AWS SSM Run Command", "url": "https://{0}.console.aws.amazon.com/systems-manager/run-command/executing-commands?region={0}" },
    # monitoring, alarming, events
    { "name": "AWS CloudTrail", "url": "https://{0}.console.aws.amazon.com/cloudtrailv2/home?region={0}#/events" },
    { "name": "AWS CloudWatch Alarms", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#alarmsV2:" },
    { "name": "AWS CloudWatch Log Groups", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#logsV2:log-groups" },
    { "name": "AWS CloudWatch Log Insights", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#logsV2:logs-insights" },
    { "name": "AWS CloudWatch Metrics", "url": "https://{0}.console.aws.amazon.com/cloudwatch/home?region={0}#metricsV2:" },
    { "name": "AWS EventBridge Rules", "url": "https://{0}.console.aws.amazon.com/events/home?region={0}#/rules" },
    { "name": "AWS EventBridge Schedules", "url": "https://{0}.console.aws.amazon.com/scheduler/home?region={0}#schedules" },
    { "name": "AWS EventBridge Pipes", "url": "https://{0}.console.aws.amazon.com/events/home?region={0}#/pipes" },
    # documentation
    { "name": "AWS CLI v2 reference", "url": "https://awscli.amazonaws.com/v2/documentation/api/latest/index.html" }
]


class Plugin(PluginInstance, GeneratorQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)
        region = self.normalise_region(self.readConfig("region", str) or "")
        self._region = region if region is not None else DEFAULT_AWS_REGION
        self.accounts_file = Path(__file__).parent / "accounts.json"

    @staticmethod
    def normalise_region(value):
        region = value.strip().lower()
        if not region:
            return DEFAULT_AWS_REGION
        if re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region):
            return region
        return None

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, value):
        region = self.normalise_region(value)
        if region is not None and region != self._region:
            self.writeConfig("region", region)
            self._region = region

    def configWidget(self):
        return [
            {"type": "label", "text": "Set the AWS region for regional service links. "
             f"Use a region code such as eu-west-1; blank input resets to {DEFAULT_AWS_REGION}. "
             "Invalid region code formats are ignored. Global and account links are unchanged."},
            {"type": "lineedit", "label": "AWS region", "property": "region",
             "widget_properties": {"placeholderText": DEFAULT_AWS_REGION}},
        ]

    def defaultTrigger(self):
        return "aws "

    def icon(self):
        return Icon.image(Path(__file__).parent / "plugin.svg")

    def load_services(self):
        region = self.region
        return self.load_accounts() + [
            {**service, "url": service["url"].format(region)}
            for service in AWS_URL_LIST]

    def load_accounts(self):
        try:
            config = json.loads(self.accounts_file.read_text(encoding="utf-8"))
            if not isinstance(config, dict):
                raise ValueError
            portal = config.get("portal_url")
            permission_set = config.get("permission_set")
            accounts = config.get("accounts")
            if (not isinstance(portal, str)
                    or any(ord(char) <= 32 or ord(char) == 127 for char in portal)
                    or any(char in portal for char in "?#\\")):
                raise ValueError
            parsed = urlsplit(portal)
            hostname = parsed.hostname
            port = parsed.port  # Access validates numeric syntax and the port range.
            if (parsed.scheme != "https" or not hostname
                    or parsed.username is not None or parsed.password is not None
                    or parsed.netloc.endswith(":") or port == 0
                    or len(hostname) > 253
                    or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                               for label in hostname.split("."))):
                raise ValueError
            authority = hostname if port is None else f"{hostname}:{port}"
            portal = urlunsplit(("https", authority, parsed.path.rstrip("/"), "", ""))
            if not isinstance(permission_set, str) or not permission_set.strip():
                raise ValueError
            if not isinstance(accounts, list):
                raise ValueError
            results = []
            seen = set()
            for account in accounts:
                if not isinstance(account, dict):
                    raise ValueError
                name, account_id = account.get("name"), account.get("id")
                if (not isinstance(name, str) or not name.strip()
                        or not isinstance(account_id, str)
                        or not re.fullmatch(r"[0-9]{12}", account_id)
                        or account_id in seen):
                    raise ValueError
                seen.add(account_id)
                parameters = urlencode({"account_id": account_id,
                                        "role_name": permission_set})
                results.append({"name": f"AWS Account: {name}",
                                "url": f"{portal}/#/console?{parameters}"})
            results.append({"name": "AWS Account Portal", "url": f"{portal}/#/"})
            return results
        except FileNotFoundError:
            return []
        except (OSError, ValueError):
            # Do not log account data, portal URLs or exception details.
            warning("Could not load accounts.json. Check the local account configuration.")
            return []

    def items(self, context):
        if not context.isValid:
            return

        aws_services_list = self.load_services()

        if not context.isValid:
            return

        query_stripped = context.query.strip().lower()

        if query_stripped:
            results = []
            for service in aws_services_list:
                if not context.isValid:
                    return
                if query_stripped in service['name'].lower():
                    results.append(StandardItem(id=f"{self.id()}/{service['url']}",
                                                text=service["name"],
                                                icon_factory=self.icon,
                                                subtext=service["url"],
                                                actions=[Action("open", "Open service URL", lambda u=service["url"]: openUrl(u))]))

            if not context.isValid:
                return
            if results:
                yield results
            else:
                yield [StandardItem(id=f"{self.id()}/no-matches",
                                    text="No service matching search string",
                                    icon_factory=self.icon)]

        else:
            yield [StandardItem(id=f"{self.id()}/search",
                                icon_factory=self.icon,
                                text="...",
                                subtext="Search for an AWS service name")]
