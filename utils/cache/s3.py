import time

import pandas as pd

from utils.cache.base import MemoCache


class S3QueryCache(MemoCache):
    """A cache that stores values in S3."""

    cache_name = "S3Query"

    def query(self, key):
        # TODO: S3 Query
        # sleep
        time.sleep(5)
        print(f'S3 Query {key}')
        return pd.DataFrame([[1, 2, 3], [4, 5, 6]], columns=['a', 'b', 'c'])


s3_query = S3QueryCache()
