# Rosbag Bazaar Client API Python Library
This package contains the client library for the Rosbag Bazaar.

## Usage

ros package for rbb client (this is automatically generated from the api specification)

```python
from __future__ import print_function
import time
import rbb_client
from rbb_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = rbb_client.BasicApi()
store_name = 'store_name_example' # str | Name of the store
bag_name = 'bag_name_example' # str | Name of the bag

try:
    # List products from bag
    api_response = api_instance.list_bag_products(store_name, bag_name)
    print(api_response)
except ApiException as e:
    print("Exception when calling BasicApi->list_bag_products: %s\n" % e)

```