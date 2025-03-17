import logging
import boto3
from botocore.exceptions import ClientError
import os
import time

def upload_file(data, bucket, object_name):
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_fileobj(data, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def download_file(bucket, file_name):
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket, file_name, file_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def download_file_from_a_nested_folder(bucket, key, file_name):
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket, key, file_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def get_s3_url(bucket, object_name):
    s3_client = boto3.client('s3')
    url = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': object_name}, ExpiresIn=3600)
    return url

def get_downloadable_links_of_a_s3_bucket(bucket):
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket)
    list_of_downloadable_files = []
    for element in response['Contents']:
        list_of_downloadable_files.append(get_s3_url(bucket, element['Key']))
    return list_of_downloadable_files

def check_if_file_exists(bucket, file_name):
    s3_client = boto3.client('s3')
    try:
        s3_client.head_object(Bucket=bucket, Key=file_name)
    except ClientError:
        return False
    return True

def get_all_ec2_instances():
    # Create an EC2 client
    ec2_client = boto3.client('ec2')

    # Describe all instances
    response = ec2_client.describe_instances()

    # Extract instances and their states
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            instances.append({'InstanceId': instance_id, 'State': state})
    
    return instances

def start_ec2_instance(instance_id):
    # Create an EC2 client
    ec2_client = boto3.client('ec2')

    # Start the instance
    try:
        ec2_client.start_instances(InstanceIds=[instance_id], DryRun=False)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def checking_if_ec2_instance_is_ready(instance_id):
    # Create an EC2 client
    ec2_client = boto3.client('ec2')

    while True:
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        statuses = response['InstanceStatuses']
        
        if not statuses:
            print("Instance is in a pending state. Waiting...")
        else:
            instance_status = statuses[0]['InstanceStatus']['Status']
            system_status = statuses[0]['SystemStatus']['Status']
            
            if instance_status == 'ok' and system_status == 'ok':
                print(f"Instance {instance_id} is fully initialized and ready.")
                break
            else:
                print(f"Instance {instance_id} is initializing. SystemStatus: {system_status}, InstanceStatus: {instance_status}")
        
        time.sleep(10)  # Wait 10 seconds before checking again
    return True
    
def send_command_and_fetch_output(
    instance_id,
    commands,
    region_name = 'us-east-1',
):
    # Create an SSM client
    ssm_client = boto3.client('ssm', region_name=region_name)

    # Send a command (e.g., list files in home directory)
    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",  # This document executes shell commands
        Parameters={'commands': commands},
    )

    # Get command ID
    # command_id = response['Command']['CommandId']
    # print(f"Command sent! Command ID: {command_id}")

    # # Wait for command to be executed
    # while True:
    #     output = ssm_client.get_command_invocation(
    #         CommandId=command_id,
    #         InstanceId=instance_id,
    #     )
    #     status = output['Status']
    #     if status == 'Success':
    #         print("Command executed")
    #         break
    #     elif status == 'Failed':
    #         print("Command failed")
    #         break
    #     else:
    #         print("Command is executing...")
    #         time.sleep(5)
    
def start_and_send_command_to_ec2_instance(
    instance_id,
    commands,
    region_name = 'us-east-1',
):
    # Start the instance
    start_ec2_instance(instance_id)

    # Wait for the instance to be ready
    checking_if_ec2_instance_is_ready(instance_id)

    # Send command and get output
    send_command_and_fetch_output(instance_id, commands, region_name)
    stop_ec2_instance(instance_id)

def stop_ec2_instance(instance_id):
    # Create an EC2 client
    ec2_client = boto3.client('ec2')

    # Stop the instance
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id], DryRun=False)
    except ClientError as e:
        logging.error(e)
        return False
    return True