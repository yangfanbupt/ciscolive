"""
this code is to clean up the AWS resources for my CSR ciscolive lab. it has following rules
1.disable instance's termination protection for matched instances (instance name starts with Pod)
2.delete transit-vpc and spoke-vpc cloudformation template for matched name (stackname starts with P)
3.delete transit and spoke vpc for matched name (VPC name starts with P)

It uses Vernhart's code (rmvpn.py) with my own modification
Vernhart's code can be found here https://gist.github.com/vernhart/c6a0fc94c0aeaebe84e5cd6f3dede4ce
"""
import boto3
import rmvpc

def disable_termination_protection(disable1, regions, dryrun):

    filters = [
                                        {
                                            'Name': 'tag-value',
                                            'Values': [
                                                'Pod*',
                                            ]
                                        },
        {
            'Name': 'instance-state-name',
            'Values': [
                'stopped',
            ]
        }
                                    ]
    for region in regions:
        ec2 = boto3.resource("ec2", region_name=region)
        instances = ec2.instances.filter(Filters=filters)
        for instance in instances:
            instance_name=''
            for tag in instance.tags:
                if tag['Key'] == 'Name':
                    instance_name = tag['Value']

            print(region, instance.instance_id, instance_name)
            instance.modify_attribute(DisableApiTermination={
                'Value': disable1
            })
            result = instance.terminate(DryRun=dryrun)
            print(result)


def delete_transit_vpc_template(region, dryrun):
    for region in regions:
        cfn = boto3.client('cloudformation', region_name=region)
        stacks = cfn.list_stacks()['StackSummaries']
        delete_stacks = []
        for stack in stacks:
            if stack['StackName'][0] == 'P':
                print(stack)
                delete_stacks.append(stack)

        if not dryrun:
            for stack in delete_stacks:
                if stack['StackStatus'] == 'CREATE_COMPLETE':
                    cfn.delete_stack(StackName=stack['StackName'])
                elif stack['StackStatus'] == 'DELETE_FAILED':
                    cfn.delete_stack(StackName=stack['StackName'], RetainResources=['VPNConfigS3Bucket'])


def delete_vpcs(region, dryrun):
    filters = [
        {
            'Name': 'tag-value',
            'Values': [
                'P*',
            ]
        },
    ]

    for region in regions:
        ec2 = boto3.resource("ec2", region_name=region)
        vpcs = ec2.vpcs.filter(Filters=filters)
        for vpc in vpcs:
            #vpc.delete(DryRun=dryrun)
            vpc_name = ''
            for tag in vpc.tags:
                if tag['Key'] == 'Name':
                    vpc_name = tag['Value']
            print(vpc_name, vpc.vpc_id)
            try:
                rmvpc.vpc_cleanup(vpc.vpc_id, region)
            except:
                print("An error occurred")


dryrun = False
regions = ['us-east-1', 'us-west-2', 'ap-southeast-1', 'eu-west-1', 'eu-central-1', 'ap-northeast-1']
enable_termination_protection = False
disable_termination_protection(enable_termination_protection, regions, dryrun)

delete_transit_vpc_template(regions, dryrun)

delete_vpcs(regions, dryrun)



