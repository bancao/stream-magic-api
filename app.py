#!flask/bin/python
from flask import Flask, jsonify, request
from minio_client import MinioClient
from apply_template import videoOverlyObjMask
from moviepy.video.io.ffmpeg_tools import ffmpeg_merge_video_audio
import uuid
import cv2
import io
import os
import json
from moviepy.editor import *
from datetime import datetime
import asyncio
import concurrent.futures


app = Flask(__name__)

minio_client = MinioClient(service="127.0.0.1:9000", access_key="AKIAIOSFODNN7EXAMPLE", secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")


@app.route('/boss/<boss>/videos', methods=['GET'])
def get_tasks(boss):
    files = minio_client.bucket_list_files(boss, "video_")
    print(files)
    return jsonify({'files': files})


@app.route('/video/templates', methods=['GET'])
def get_templates():
    files = minio_client.bucket_list_files("template", "video_")
    print(files)
    return jsonify({'files': files})


@app.route('/boss/<boss>/merge-stream', methods=['POST'])
def merge_streams(boss):
    files = minio_client.bucket_list_files(boss, "")
    print(files)
    return jsonify({'files': files})


@app.route('/boss/<boss>/upload', methods=['GET'])
def upload_file(boss):
    base_folder = "/Users/shengbincao/myspace/stream-magic/videos/"
    file_name = ""
    for idx in range(1, 13):
        if idx < 10:
            file_name = "0%d.mp4" % idx
        else:
            file_name = "%d.mp4" %idx
        minio_client.upload_file(boss, "video_" +file_name, base_folder + file_name, "video/mp4")
        save_video_cover(boss, base_folder + file_name, "img_" + file_name.replace(".mp4", ".jpeg"))
    return jsonify({'files': ""})


@app.route('/boss/<boss>/<client>/concat', methods=['POST'])
def concat_files(boss, client):
    request_data = request.get_data(as_text=True)
    select_items = json.loads(request_data).get("files")
    print(select_items)
    files = []
    for item in select_items:
        print("-----")
        print(item)
        if isinstance(item, str):
            files.append(item)
        else:
            files.append(item.get("videoUrl"))
    print("======")
    print(files)
    concat_name = concat_videos(files)
    save_name = "client_" + boss + "_" + client + "-"+ str(uuid.uuid1()) +".mp4"
    minio_client.upload_file(boss, save_name, concat_name, "video/mp4")
    os.remove(concat_name)
    response_headers = {"response-content-type": "video/mp4"}
    video_url = minio_client.presigned_get_file(boss, save_name, 1, response_headers)
    return jsonify({'videoUrl': video_url})


def save_video_cover(bucket, video_file_name, image_name):
    vidcap = cv2.VideoCapture(video_file_name)
    cv2.VideoCapture()
    success, image = vidcap.read()
    n = 1
    while n < 30:
        success, image = vidcap.read()
        n += 1
    print(image.size)
    _, JPEG = cv2.imencode('.jpeg', image)
    raw_img = io.BytesIO(JPEG.tobytes())
    raw_img_size = raw_img.getbuffer().nbytes
    minio_client.upload_byte_file(bucket, image_name, raw_img, raw_img_size, "application/octet-stream")


def concat_videos(files):
    print(datetime.now())
    video_clips = create_video_clips(files)
    print(datetime.now())
    # final_clip = videoOverlyObjMask(files[0], "video", files[1])
    final_clip = concatenate_videoclips(video_clips, method='compose')
    random_file_name = "/Users/shengbincao/myspace/stream-magic/videos/" + str(uuid.uuid1()) + ".mp4"
    print(datetime.now())
    print("start to write")
    final_clip.write_videofile(random_file_name, fps=24, verbose=False, logger=None, remove_temp=True, threads=32)
    print(datetime.now())
    print("end to write")
    return random_file_name


def create_video_clip(file):
    video = VideoFileClip(file, target_resolution=(540, 960))
    return video

def create_video_clips(files):
    video_clips = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Start the load operations and mark each future with its URL
        video_clip_futures = {executor.submit(create_video_clip, file): file for file in files}
        for future in concurrent.futures.as_completed(video_clip_futures):
            video_clips.append(future.result())
    return video_clips


if __name__ == '__main__':
    app.run(debug=True)