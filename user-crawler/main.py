import logging
import logging.handlers
import os
import sys
from lib.storage import Storage
from lib.twitter import Twitter


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.DEBUG,
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                filename=os.path.join(data_dir, 'app.log'),
                maxBytes=10*1024*1024,
                backupCount=3,
                encoding='utf-8',
            ),
        ],
    )

    logging.info("Started")

    try:
        storage = Storage(data_dir)
        twitter = Twitter(data_dir)

        user = storage.select_user()

        if not user:
            if len(sys.argv) < 2:
                raise Exception(f"Usage: {sys.argv[0]} [INITIAL_USERNAME]")
            user = twitter.get_user_by_name(sys.argv[1])

        followings = twitter.get_followings(user['id'])

        storage.save_followings(user, followings)

        # TODO: retrieve and save followers

        # TODO: delete nonexistent users

        storage.save_stats()
    except Exception as e:
        logging.exception(str(e))
        sys.exit(1)

    logging.info("Finished")


if __name__ == '__main__':
    main()
