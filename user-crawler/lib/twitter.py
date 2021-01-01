import json
import logging
import os
import time
import urllib.request
import urllib.parse

API_RETRY_MAX = 15


class Twitter:

    ERROR_NOT_FOUND = 'https://api.twitter.com/2/problems/resource-not-found'

    def __init__(self, data_dir):
        self.data_dir = data_dir

    def call_api(self, endpoint, params=None):
        headers = {
            'Authorization': ("Bearer " +
                              os.environ['TWITTER_API_BEARER_TOKEN']),
        }

        if params:
            endpoint += '?' + urllib.parse.urlencode(params)

        logging.debug(f"call api: {endpoint}")

        for i in range(API_RETRY_MAX):
            req = urllib.request.Request(endpoint, headers=headers)

            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read())

                break
            except urllib.error.HTTPError:
                if i >= API_RETRY_MAX - 1:
                    raise

                logging.debug(f"retry api call (sleep {2 ** i} secs)")

                time.sleep(2 ** i)

        logging.debug(f"{data}")

        return data

    def get_user_by_name(self, username):
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        params = {
            'user.fields': ','.join([
                'created_at',
                'description',
                'entities',
                'id',
                'location',
                'name',
                'pinned_tweet_id',
                'profile_image_url',
                'protected',
                'public_metrics',
                'url',
                'username',
                'verified',
                'withheld',
            ]),
        }

        data = self.call_api(url, params)

        if any(e['type'] == self.ERROR_NOT_FOUND
               for e in data.get('errors', [])):
            return None

        return data['data']

    def get_followings(self, user_id):
        """Get followings of specified user
        """
        next_token = None
        while True:
            url = f"https://api.twitter.com/2/users/{user_id}/following"
            params = {
                'user.fields': ','.join([
                    'created_at',
                    'description',
                    'entities',
                    'id',
                    'location',
                    'name',
                    'pinned_tweet_id',
                    'profile_image_url',
                    'protected',
                    'public_metrics',
                    'url',
                    'username',
                    'verified',
                    'withheld',
                ]),
                'max_results': 1000,
                **({} if next_token is None else
                   {'pagination_token': next_token}),
            }

            data = self.call_api(url, params)

            if data['meta']['result_count'] > 0:
                for following in data['data']:
                    yield following

            next_token = data['meta'].get('next_token')
            if not next_token:
                break
