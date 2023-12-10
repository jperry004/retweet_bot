"""
This module contains functions for downloading, processing, and analyzing
videos from Twitter, with a specific focus on detecting the presence of ties
in video frames. It is designed to be imported and its functions utilized in
other scripts or interactive sessions.

Key Functionalities:
- Download videos from Twitter using tweet IDs.
- Downsample videos for efficient processing.
- Load and utilize YOLO model for object detection.
- Detect neck ties in video frames.
- Analyze videos for neck tie presence.
- Calculate video length.
- Provide an integrated approach for neck tie detection in Twitter videos.

Dependencies:
- cv2 (OpenCV): For video processing and YOLO model interfacing.
- numpy: For numerical operations.
- os and time: For file and time handling.
- twitter_video_dl: For downloading videos from Twitter.

Each function in this module can be used independently or in combination to
facilitate the analysis of Twitter videos, particularly for object detection
tasks like identifying if a person in a video is wearing a tie.
"""



import cv2
import numpy as np
import os
import time
from twitter_video_dl.twitter_video_dl import download_video


TIE_TIMEOUT = 60
path = '/home/josh/repos/suit_detector/'
weights_path = path + "yolov4.weights"
cfg_path = path + "yolov4.cfg"
class_names_path = path + "coco.names"


# 'https://twitter.com/i/web/status/1537233988523286530'

def download_tweet_video(tweet_id):
    """
    Downloads the video from a tweet using its tweet ID.

    Args:
    - tweet_id (str): The ID of the tweet.

    Returns:
    - str: The filename of the downloaded video.
    """

    # Construct the tweet URL from the tweet ID
    tweet_url = f'https://twitter.com/web/status/{tweet_id}'
    filename = f'{tweet_id}.mp4'
    if filename not in os.listdir():
        download_video(tweet_url, filename)
        print(f'\nDL and wrote {filename}')
    return filename


def downsample_video(video_path: str):
    """
    Downsamples a video to reduce its frame rate.

    Args:
    - video_path (str): The path of the video to be downsampled.

    Returns:
    - str: The filename of the downsampled video.
    """

    # Get the base file name (without the extension)
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Generate the output file name
    output_name = base_name + '-downsampled.mp4'

    # Open the video using OpenCV
    video = cv2.VideoCapture(video_path)

    # Get the video's width, height, and number of frames
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video.get(cv2.CAP_PROP_FPS))
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video_length = frame_count / fps  # in seconds

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    if video_length > 60:  # If video is longer than 1 minute
        out_fps = 0.5  # Downsample to 0.5 frames per second
    else:
        out_fps = 1  

    out = cv2.VideoWriter(output_name, fourcc, out_fps, (width, height))

    # Read the first frame
    ret, frame = video.read()

    # Keep track of the frame number
    frame_number = 1

    # Loop until the end of the video
    while ret:
        # Write the frame to the output video if it is a multiple 
        if frame_number % int(fps/out_fps) == 0:
            out.write(frame)

        # Read the next frame
        ret, frame = video.read()

        # Increment the frame number
        frame_number += 1

    # Release the VideoWriter and VideoCapture objects
    out.release()
    video.release()
    return output_name






def load_yolo_model(weights_path, cfg_path):
    """
    Loads the YOLO model from given weights and configuration files.

    Args:
    - weights_path (str): Path to the YOLO model weights file.
    - cfg_path (str): Path to the YOLO model configuration file.

    Returns:
    - tuple: The loaded YOLO network and output layer names.
    """

    net = cv2.dnn.readNet(weights_path, cfg_path)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in 
                     net.getUnconnectedOutLayers().flatten().tolist()]
    return net, output_layers


def detect_tie(net, output_layers, frame, conf_threshold=0.5):
    """
    Detects if there is a tie in the given frame using the YOLO model.

    Args:
    - net: The loaded YOLO network.
    - output_layers: The output layers of the YOLO network.
    - frame: The image frame to be analyzed.
    - conf_threshold (float, optional): The confidence threshold for detection.

    Returns:
    - bool: True if a tie is detected, False otherwise.
    """

    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, 
                                 crop=False)
    net.setInput(blob)
    layer_outputs = net.forward(output_layers)

    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            coco_tie_class_id = 27
            if confidence > conf_threshold and class_id == coco_tie_class_id:  
                return True
    return False

def is_person_wearing_tie(video_path):
    """
    Checks if any person is wearing a tie in the video.

    Args:
    - video_path (str): The path of the video to be analyzed.

    Returns:
    - bool: True if a person wearing a tie is detected, False otherwise.
    """

    net, output_layers = load_yolo_model(weights_path, cfg_path)
    
    cap = cv2.VideoCapture(video_path)

    start_time = time.time()  # Start measuring execution time
    while cap.isOpened():
        # Check if the elapsed time is greater than 30 seconds
        elapsed_time = time.time() - start_time
        if elapsed_time > TIE_TIMEOUT:
            print('\nTimed out checking for tie, sending false')
            # If it times out - skip it, so pretend we found a tie
            return False
            

        ret, frame = cap.read()
        if not ret:
            break

        if detect_tie(net, output_layers, frame):
            cap.release()
 #           print("Someone is wearing a tie in the video")
            return True

    cap.release()
    #print("No one is wearing a tie in the video")
    return False


def get_video_length(video_path):
    """
    Calculates the length of a video in seconds.

    Args:
    - video_path (str): The path of the video.

    Returns:
    - float: The length of the video in seconds.
    """

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    length = frame_count / fps
    cap.release()
    return length

def tie_detector(tweet_id):
    """
    Detects if there is a tie in a video from a tweet.

    Args:
    - tweet_id (str): The ID of the tweet.

    Returns:
    - bool or None: True if a tie is detected, False if not, or None if error
    """

    #start_time = time.time()  # Start measuring execution time
    try:
        location = download_tweet_video(tweet_id)
    except AssertionError as e:
        print('Error downloading', e)
        return None
    downsampled_video = downsample_video(location)
    print('\nChecking for tie')
    result = is_person_wearing_tie(downsampled_video)

    # List all files in the directory
    files = os.listdir()
    # Loop through each file and delete mp4 files that contain tweet_id
    for file in files:
        if file.endswith(".mp4"):
            os.remove(file)
    return result





































