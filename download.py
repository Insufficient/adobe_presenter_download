import requests, sys, subprocess, os, glob, shutil, re
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError

SETTINGS = {
    # Removes the temporary audio/video parts once the process is finished.
    # Note: This should not be used if no lecture slides are used
    "CLEAN_UP": False,
    # A slower preset will provide better compression (compression is quality per filesize)
    # Available options: ultrafast, superfast, veryfast, faster, fast, medium, 
    #                    slow, slower, veryslow
    "FFMPEG_PRESET": "superfast",
    "FILTER_SILENCE": True,
}

# Moodle specific
LOGIN_FAILURE_MSG = "You are not logged in."

# Users can get the link by typing into the browser console
# 'document.getElementById( 'resourceobject' ).src'
def get_link():
    url = input("Adobe Presenter Base URL: ")
    return url.replace('"', "").replace("index.htm", "").replace("?embed=1", "").strip()


def get_cookie():
    (c_key, c_val) = (input("Cookie Key: "), input("Cookie Value: "))
    # defaults to MoodleSession if c_key not provided
    if c_key == "":
        c_key = "MoodleSession"
    return {c_key: c_val}


def mp3_name(idx):
    return f"a24x{idx}.mp3"


# Get duration of a single mp3
def get_mp3_duration(file_name):
    args = ["ffprobe", "-show_entries", "format=duration", "-i", f"{file_name}"]
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if popen.wait() == 0:
        results = popen.stdout.read().decode("utf-8")
        dura = float(results.split("\n")[1].strip().split("=")[1])
        return int(dura)
    return 0


# Get the duration of each mp3 part
def get_part_durations(folder):
    return [
        get_mp3_duration(file)
        for file in sorted(glob.glob(f"{folder}/{mp3_name('*')}"), key=os.path.getmtime)
    ]


# ffmpeg removesilence filter to get rid of the annoying static click
# at the beginning of each mp3 part
def mp3_filter(mp3_name):
    mp3_name = mp3_name.replace(".mp3", "")
    args = [
        "ffmpeg",
        "-i",
        f"{mp3_name}.mp3",
        "-af",
        (
            "silenceremove=start_periods=1:start_duration=1:start_threshold=-60dB:"
            + "detection=peak,aformat=dblp,areverse,silenceremove=start_periods=1:start_"
            + "duration=1:start_threshold=-60dB:detection=peak,aformat=dblp,areverse"
        ),
        "-ab",
        "96k",
        f"{mp3_name}a.mp3",
    ]
    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(f"{mp3_name}a.mp3", f"{mp3_name}.mp3")


# Combine mp3 parts as a single mp3
def combine_mp3(file_name):
    args = "concat:" + "|".join( glob.glob( f"{file_name}/{mp3_name('*')}" ) )
    subprocess.run(
        ["ffmpeg", "-y", "-i", args, "-codec", "copy", f"{file_name}/audio.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# Save input.txt that contains the duration of each slide which will be fed into ffmpeg
def save_ffmpeg_input(file_name, durations):
    out = ""
    for (idx, d) in enumerate(durations):
        out = f"{out}file 'slide{idx}.png'\nduration {d}\n"

    # ffmpeg quirk requires last line to be the last slide repeated
    out = f"{out}file 'slide{idx}.png'\n"
    with open(f"{file_name}/input.txt", "w+") as i_f:
        i_f.write(out)


# Save pdf as a collection of images
def save_as_images(file_name):
    try:
        images = convert_from_path(file_name + ".pdf")
        for (idx, img) in enumerate(images):
            img.save(file_name + "/slide" + str(idx) + ".png")
        return len(images)

    # catch files that don't exist and invalid files!
    except PDFPageCountError:
        print("Invalid PDF file")
    return 0


# Combine collection of images as a video
def combine_images(file_name):
    params = [
        "ffmpeg",
        "-f",
        "concat",
        "-i",
        file_name + "/input.txt",
        "-preset",
        SETTINGS[ "FFMPEG_PRESET" ],
        "-vf",
        "scale=-2:720,format=yuv420p",
        "-y",
        f"{file_name}/video.mp4",
    ]
    subprocess.run(params, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Combine video of slides and audio into a final video
def combine_final(file_name):
    params = [
        "ffmpeg",
        "-i",
        f"{file_name}/video.mp4",
        "-i",
        f"{file_name}/audio.mp3",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-strict",
        "experimental",
        "-y",
        f"{file_name}.mp4",
    ]
    subprocess.run(params, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download_mp3( output, start_url, idx, cookies):
    file = mp3_name(idx)
    url = f"{start_url}/{file}"
    r = requests.get(url, cookies=cookies)

    # we found last part of mp3
    if r.status_code == 404:
        return -1

    # ensures the the type of the response is a mp3 and not plain text
    if not r.encoding:
        with open(f"{output}/{file}", "wb") as f:
            f.write(r.content)
    else:
        if r.text.find(LOGIN_FAILURE_MSG):
            print("Failed to log into Moodle, please re-enter cookies")
        sys.exit(1)

# Download mp3 parts
def download(base_url, output, cookies):
    idx = 1
    start_url = base_url + "/data/"
    if not os.path.exists(output):
        os.makedirs(output)

    # since the audio file indexes sometimes are out of order, we have to 
    # scrape the correct indexes.

    r = requests.get( f"{start_url}/html/Project.js", cookies=cookies )
    if r.status_code == 404:
        # fallback to old method of obtaining mp3 parts

        # download mp3 parts by iterating from 1.... until 404 Not Found
        while True:
            if download_mp3( output, start_url, idx, cookies ) == -1:
                break
            idx += 1
    else:
        files = sorted( re.findall( r'a24x([0-9]+)\.mp3', r.text ), key=int )
        for i in files:
            download_mp3( output, start_url, i, cookies )


def clean_up(file_name):
    try:
        shutil.rmtree(file_name)
    except FileNotFoundError:
        pass


def main():
    cookies = get_cookie()

    output = input("Output/PDF Name: ")

    while output:
        link = get_link()
        print("Downloading mp3 parts")
        idx = download(link, output, cookies)
        print("Parts downloaded, combining mp3 parts")

        if SETTINGS["FILTER_SILENCE"]:
            print("will first filter for silence..")
            for mp3 in sorted(
                glob.glob(f"{output}/{mp3_name('*')}"), key=os.path.getmtime
            ):
                mp3_filter(mp3)

        combine_mp3(output)
        print("Parts combined")
        if os.path.isfile(output + ".pdf"):
            print("Splitting PDF into collection of images")
            save_as_images(output)
            dura = get_part_durations(output)
            save_ffmpeg_input(output, dura)

            print("Combining images into a video")
            combine_images(output)

            print("Combining video with audio")
            combine_final(output)

            if SETTINGS["CLEAN_UP"]:
                print("Cleaning up")
                clean_up(output)
            print("Finished.")
        else:
            print(
                f"Lecture slides not included, combined mp3 is located at: {output}/audio.mp3"
            )
        output = input("Output/PDF Name: ")

main()
