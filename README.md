# s3_env_stats
Lists total number of objects and total bucket size for targat AWS account and region.   
Uses CloudWath 1w metrics.
Requires AWS profile and region as input.
## Usage
./s3_env_stats.py profile-name region-name
## Output
```shell
Name              Objects    Size
bucket-name       X          Z.YGB
~~~~
List of buckets inside other regions
~~~~
Total number of buckets found : X
Total number of objects found : Y
Total size: Q.W GB
```
