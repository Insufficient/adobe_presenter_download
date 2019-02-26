## Intro
Adobe Presenter splits audio recordings for each slide making it difficult to seek to a certain point in a presentation and alter the playback speed of the presentation. This script will allow the audio recordings to be downloaded and combined into a single mp3 file allowing the change of playback speed and easier seeking. This script also allows lecture slides to be provided which will output the presentation as a video (mp4).

## Notes
This project heavily relies on the audio files to be in a specific directory, with a specific file name and may only work for certain courses hosted on UNSW Moodle.

## Instructions
Using PSYC1022 (UNSW) as an example
1) Login to UNSW Moodle
2) Open "Developer Tools" (F12), go to *storage* tab and check for your MoodleSession value
3) Navigate to the page containing the lecture slides, type below in the *console* tab to get the Presenter URL
> document.getElementById( 'resourceobject' ).src
4) Run download.py, the first input will be your cookie key (just press enter for "MoodleSession"), second is your cookie value, third is your desired output filename (name of lecture slides), fourth is the Presenter URL.
5) You should see audio.mp3 in your output_name folder if you did not provide lecture slides, if you provided lecture slides, they should be in your current directory as output_name.mp4


Example:
``` 
Cookie Key: MoodleSession
Cookie Value: q0xxxxxxxxxxxxxxxgxxxx7
Output/PDF Name: Lec1
Adobe Presenter Base URL: "https://moodle.telt.unsw.edu.au/pluginfile.php/3941393/mod_resource/content/10/index.htm?embed=1"
```


## Requirements
- Python 3.6
- ffmpeg/ffprobe binaries