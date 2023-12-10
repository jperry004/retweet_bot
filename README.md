# Ukraine War Retweets Bot

This Python-based Twitter bot is designed for automated retweeting of videos related to the Ukraine war. It's equipped with content filtering, verification, and tweet management capabilities. The project includes a fork of [inteoryx/twitter-video-dl](https://github.com/inteoryx/twitter-video-dl) for video downloading functionalities.

## Features

- **Automated Tweet Processing**: Identifies and processes tweets containing Ukraine war-related videos.
- **Deletion Check**: Verifies if tweets are deleted before processing.
- **Database Management**: Uses TinyDB for efficient tweet data management.
- **Error and Rate Limit Handling**: Smartly handles Twitter API rate limits and errors.

## How It Works

The bot monitors Twitter for relevant content, performing checks for content relevance, deletion verification, and database updates to manage tweet statuses and avoid redundancy.

## Installation

1. **Clone the Repository**: `git clone https://github.com/jperry004/ukraine-war-retweets-bot.git`
2. **Install Dependencies**: `pip install -r requirements.txt`

## Usage

1. **Setup API Keys**: Fill in your Twitter API keys and tokens in the script.
2. **Run the Bot**: `python run_script.py`
3. **Monitor Output**: Observe the bot's processing logs.

## Dependencies

- Python 3.x
- tweepy
- tinydb
- requests

## YOLO Weights (Not Included)

Please note that the YOLO (You Only Look Once) weights for object detection used in this project are not included in this repository due to their large file size. To use this project, you can obtain standard YOLO v4 weights separately.

Here's how you can obtain standard YOLO v4 weights:

1. Visit the official YOLO website or repository to find the latest YOLO v4 weights: [YOLO Repository](https://github.com/AlexeyAB/darknet).

2. Follow the instructions provided in the YOLO repository to download the YOLO v4 weights.

3. Place the downloaded YOLO v4 weights in the appropriate directory or specify the path to these weights in your project configuration.

Please ensure that you have the required YOLO v4 weights before running the object detection component of this project.

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests.

## License

This project is licensed under the [Unlicense](LICENSE), a public domain equivalent license.

## Disclaimer

This bot is for educational and informational purposes related to the Ukraine war and adheres to Twitter's policies.

## Acknowledgments

Thanks to the contributors of the open-source libraries used in this project, including a fork from [inteoryx/twitter-video-dl](https://github.com/inteoryx/twitter-video-dl).

---

