#!/usr/bin/env python3

import boto3
import sys
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

def get_cnt(lVals):
        d = dict(zip(lVals, [0] * len(lVals)))
        for x in lVals:
            d[x] += 1
        return d

def connect_aws(vvProfile,vvRegion,vvService):
    try:
        boto3.setup_default_session(profile_name=vvProfile,region_name=vvRegion)
        worker = boto3.client(vvService)
        return worker
    except ClientError as e:
        print(e)

def get_bucket_size(vvWorker,vvBucketName): 
    try:
        response = vvWorker.get_metric_statistics( Namespace="AWS/S3", MetricName="BucketSizeBytes", Dimensions=[ { "Name": "BucketName", "Value": vvBucketName }, { "Name": "StorageType", "Value": "StandardStorage" } ], StartTime=datetime.now() - timedelta(days=7), EndTime=datetime.now(), Period=86400, Statistics=['Average'])
        return response
    except ClientError as e:
        print(e)

def get_object_count(vvWorker,vvBucketName): 
    try:
        response = vvWorker.get_metric_statistics( Namespace="AWS/S3", MetricName="NumberOfObjects", Dimensions=[ { "Name": "BucketName", "Value": vvBucketName }, { "Name": "StorageType", "Value": "AllStorageTypes" } ], StartTime=datetime.now() - timedelta(days=7), EndTime=datetime.now(), Period=86400, Statistics=['Average'])
        return response
    except ClientError as e:
        print(e)

def get_bucket_list(vvWorker): 
    try:
        response = vvWorker.list_buckets()
        return response
    except ClientError as e:
        print(e)

def check_args():
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} profile-name region-name')
        exit()

#
# MAIN STARTS HERE
#

if __name__ == '__main__':
    #
    # Check number of arguments
    #
    check_args()
    #
    # Set vars
    #
    vProfile=sys.argv[1]
    vRegion=sys.argv[2]
    vMainList=[]
    vSideList=[]
    vTotalSize=0.0
    vTotalObject=0.0

    #
    # Connect to AWS
    #
    worker_s3=connect_aws(vProfile,vRegion,'s3')
    worker_cloudwatch=connect_aws(vProfile,vRegion,'cloudwatch')

    #
    # Get List of S3 buckets
    #
    result=get_bucket_list(worker_s3)
    for item in result['Buckets']:
        try:
            region_result=worker_s3.get_bucket_location(Bucket=item['Name'])
            vLocationHolder=region_result['LocationConstraint']
            vNameHolder=item['Name']
            #
            # For us-east-1 region, bucket location returns empty/none
            # This is what we are trying to fix here
            #
            if not vLocationHolder:
                vLocationHolder='us-east-1'
            #
            # Take action on buckets inside target region
            #
            if vRegion == vLocationHolder:
                #
                vBucketSizeResponse=get_bucket_size(worker_cloudwatch,vNameHolder)
                if vBucketSizeResponse['Datapoints'] == []:
                    vSizeHolder=0
                else:
                    vSizeHolder=vBucketSizeResponse['Datapoints'][0]['Average']
                #
                vObjectCountResponse=get_object_count(worker_cloudwatch,vNameHolder)
                if vObjectCountResponse['Datapoints'] == []:
                    vObjectHolder=0
                else:
                    vObjectHolder=vObjectCountResponse['Datapoints'][0]['Average']
                #
                vMainList.append({'Name': vNameHolder, 'Size': vSizeHolder, 'Object': vObjectHolder})
            else:
                vSideList.append({'Name': vNameHolder, 'Location': vLocationHolder})
        except ClientError as e:
            print(e)
    print(f'{"Name":<80s} {"Objects":<10s} {"Size":<10s}')
    for item in vMainList:
        vTotalSize= vTotalSize + item['Size']
        vTotalObject= vTotalObject + item['Object']
        print(f'{item["Name"]:<80s} {int(item["Object"]):<10d} {round(float(item["Size"])/1000000000,2)}GB')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    for item in vSideList:
        print(f'{item["Name"]:<80s} is in {item["Location"]:<20s}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'Total number of buckets checked : {len(vMainList)+len(vSideList)}')
    print(f'Total number of objects found : {int(vTotalObject):,}')
    print(f'Total size: {round(vTotalSize/1000000000,2)} GB')
