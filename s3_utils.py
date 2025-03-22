import logging
import boto3
from botocore.exceptions import ClientError
import os
import time
import datetime

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

def count_number_of_updated_published_books(bucket):
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket)

    projects = []

    if "Contents" in response:
        for obj in response["Contents"]:
            projects.append(obj["LastModified"])  # Timezone-aware datetime

    # Use timezone-aware datetime for calculations
    now = datetime.datetime.now(datetime.timezone.utc)

    last_24_hours = 0
    last_48_hours = 0
    last_72_hours = 0
    last_96_hours = 0
    last_120_hours = 0
    
    last_7_days = 0
    last_14_days = 0
    last_21_days = 0
    last_28_days = 0
    last_35_days = 0
    
    last_1_month = 0
    last_2_months = 0
    last_3_months = 0
    last_4_months = 0
    last_5_months = 0

    for time in projects:
        # Calculate the time difference
        time_difference = now - time  # Both are timezone-aware
        days_difference = time_difference.days
        
        if days_difference <= 0:
            last_24_hours += 1
        if days_difference <= 1:
            last_48_hours += 1
        if days_difference <= 2:
            last_72_hours += 1
        if days_difference <= 3:
            last_96_hours += 1
        if days_difference <= 4:
            last_120_hours += 1
        if days_difference <= 7:
            last_7_days += 1
        if days_difference <= 14:
            last_14_days += 1
        if days_difference <= 21:
            last_21_days += 1
        if days_difference <= 28:
            last_28_days += 1
        if days_difference <= 35:
            last_35_days += 1
        if days_difference <= 30:
            last_1_month += 1
        if days_difference <= 60:
            last_2_months += 1
        if days_difference <= 90:
            last_3_months += 1
        if days_difference <= 120:
            last_4_months += 1
        if days_difference <= 150:
            last_5_months += 1
            
    data_in_days = [
        last_24_hours,
        last_48_hours - last_24_hours,
        last_72_hours - last_48_hours,
        last_96_hours - last_72_hours,
        last_120_hours - last_96_hours,
    ]

    data_in_weeks = [
        last_7_days,
        last_14_days - last_7_days,
        last_21_days - last_14_days,
        last_28_days - last_21_days,
        last_35_days - last_28_days,
    ]

    data_in_months = [
        last_1_month,
        last_2_months - last_1_month,
        last_3_months - last_2_months,
        last_4_months - last_3_months,
        last_5_months - last_4_months,
    ]
             
    
    return {
        "data_by_days": data_in_days,
        "data_by_weeks": data_in_weeks,
        "data_by_months": data_in_months
    }