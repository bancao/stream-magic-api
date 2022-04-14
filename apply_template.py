from moviepy.editor import *


def videoOverlyObjMask(videoFName, objType='self', obj=None):
    """
    剪辑自身叠加一个该剪辑旋转的层，旋转层带自身转换的遮罩剪辑
    :param videoFName: 剪辑来源视频文件
    :return: 参数视频剪辑自身叠加一个该剪辑旋转层剪辑
    """
    clip = VideoFileClip(videoFName, audio=True)
    objClip = clip
    if objType == 'img':
        objClip = convertPicToVideo(obj, duration=clip.duration, createMask=False).set_fps(clip.fps)
    elif objType == 'video':
        if isinstance(obj, str):
            objClip = VideoFileClip(obj, audio=False)
        else:
            objClip = obj

    # rotateClip = objClip.rotate(50, expand=True).fx(vfx.resize, clip.size)
    rotateClip = objClip.fx(vfx.resize, clip.size)
    maskclip = rotateClip.to_mask()
    rotateClip = rotateClip.set_mask(maskclip)

    clipVideo = CompositeVideoClip([clip, rotateClip])
    return clipVideo


if __name__ == '__main__':
    # 实现剪辑和自身旋转剪辑叠加
    result2 = videoOverlyObjMask(r"/Users/shengbincao/myspace/stream-magic/videos/02.mp4", "video", r"/Users/shengbincao/myspace/stream-magic/videos/08.mp4")
    result2.write_videofile(r"/Users/shengbincao/myspace/stream-magic/videos/0000000.mp4", threads=8)