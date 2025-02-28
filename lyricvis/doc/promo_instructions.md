# How to create a lyricvis video

Process to create a new video:

1. Identify and download song

2. Create and upload a video to verify copyright

3. Download lyrics

4. Create song file with lyrics and timestamps, iterate on timing

5. Create title graphic

6. Generate video

7. Upload


# How was the promotion video created?

Requirement: create 45 second promo clip

Step 1:
    - identify 3-5 songs for the video
    - obtain the audio
    - determine the clips of the songs desired and their lyrics
    - create the final audio file
    - create the video:
        - create the JSON that describes the song (including the lyrics and their timestamps)
        - create a cover graphic
        - run the generator


For the 45 second promo video the song selection is shown below:


Song 1:

    R3HAB, INNA, Sash! – Rock My Body
    https://www.youtube.com/watch?v=aYCuEONIIDM


    command: yt-dlp --extract-audio --audio-format mp3 https://www.youtube.com/watch?v=aYCuEONIIDM
    command: mv {from} r3hab_rockmybody.mp3


    00:01 Baby, I need you till the morning
    00:04 I hear my body calling
    00:05 So keep the party rocking all night
    00:09 Baby, oh, we can skip the talking
    00:11 You know there's only one thing tonight
    00:15 So won't you come rock my body?


Song 2:

    Tiësto - Lay Low
    https://www.youtube.com/watch?v=8PgDeK4x_Xw

    command: yt-dlp --extract-audio --audio-format mp3 https://www.youtube.com/watch?v=8PgDeK4x_Xw
    command: mv {from} tiesto_laylow.mp3


    0:17 Lay low, hit the sun
    0:18 Everybody have a real good time
    0:21 Real good time (surround me)
    0:25 Yeah, we cool, yeah, we drunk
    0:27 Lost my mind and, baby, I feel high
    0:30 I feel high (they're calling on me)


Song 3:
    ZHU - Faded
    https://www.youtube.com/watch?v=CVvJp3d8xGQ

    command: yt-dlp --extract-audio --audio-format mp3 https://www.youtube.com/watch?v=CVvJp3d8xGQ
    command: mv {from} zhu_faded.mp3


    0:33 Baby, I'm wasted
    0:36 All I wanna do is drive home to you
    0:40 Baby, I'm faded
    0:44 All I wanna do is take you downtown