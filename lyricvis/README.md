# Overview:

LyricVis is all about pushing the boundaries of creativity – using Text-to-Image AI video generation based on song lyrics! Imagine turning lyrics into mesmerizing visuals, bringing the essence of music to life in a whole new way.

# Processing Overview:

For each lyric phrase and time code, generate an image
Stich them together to music

Input:
	file with lyrics and timestamps
	song file

Assumptions: assume 1080p (1920x1080)

# Installation:

There are two components to the installation: 1. Stable Diffusion to generate images and 2. a Python application "lyricvis" to call Stable Diffusion for images and create a video.

## Stable Diffusion:

1. Install Stable Diffussion and AUTOMATIC1111 locally.
	Instructions: https://github.com/AUTOMATIC1111/stable-diffusion-webui

2. Enable api mode:
	Run webui with --api commandline argument, for example in your "webui-user.bat": set COMMANDLINE_ARGS=--api

2. Launch sd.webui (on Windows run "run.bat")

## lyricvis:

The instructions below have been tested on a Windows 11 host using Python 3.13.0. Search on the web for "python virtualenv" for detailed instructions.

1. Install a virtual environment named "lvenv"
	python -m venv lvenv

2. Activate the virtual environment:
	.\lvenv\Scripts\Activate.bat (command prompt)
	OR
	.\lvenv\Scripts\Activate.ps1 (PowerShell)

3. Install required packages:
	pip install moviepy==1.0.3 

	Note: edit lvenv\Lib\site-packages\moviepy\video\fx\resize.py and change Image.ANTIALIAS to Image.LANCZOS

4. Create temp directories and files:
	mkdir C:\temp\lyric_vis
	mkdir C:\temp\lyric_vis\temp
 	copy .\assets\blank_640x480.png C:\temp\lyric_vis\temp\

5. ImageMagick: https://imagemagick.org/

	Note: ImageMagick 7.1.1 has been tested

	a. Download ImageMagick (this example assumes the installation file: ImageMagick-7.1.1-47-Q16-HDRI-x64-dll.exe)
	b. Install ImageMagick
	c. Edit config.json to include the path to mackick.exe
	d. Run the following to verify install of ImageMagick:
		python .\create_image_test.py

6. Configure the URL to the AUTOMATIC1111 URL in config.json

7. Configure paths in create_image_sequence.py
    IMAGE_ROOT_PATH
	IMAGE_TEMP_DIR

8. Verify the connectivity between LyricVis and Stable Diffusion:
		python .\create_image_test_sd.py



# Running:


1. Start AUTOMATIC1111:
	C:\opt\sd.webui> .\run.bat

	Configuration in webui/webui-user.bat (IP address)
		Noteable options: 
			set COMMANDLINE_ARGS=--lowram --api --server-name={ip_address}
			set CUDA_VISIBLE_DEVICES=0  # index(es) of sepecific GPUs

	Configuration options in webui/modules/cmd_args.py

2. Create assets that describe the video to create (see doc/promo_instructions.md)

3. Configuration:

    Parameters for execution:
        TARGET_VIDEO_PATH - path of generated video
        GEN_IMAGES - boolean (True or False) determines to regenerate images for each frame or not
		VIDEO_MODE - 'Text' generate text frames from lyrics or 'Image' to use generative AI image generation


4. Generate a video for a song on localhost:
	Start the virtualenv:
		pipenv shell
	Run the generator:
		python .\create_image_sequence.py

# Caveats

I've only run this on a limited amount of hardware (client running on a Windows 10 host with Stable Diffusion running on a Windows 11 host with a RTX 30 series GPU). As a result, there are likely a few references
to directories that may not exist and are certainly not platform agnostic. If you fix these please send a patch.


# TODO:

Update moviepy from 1.x to 2.x:
https://zulko.github.io/moviepy/getting_started/updating_to_v2.html#moviepy-editor-supression-and-simplified-importation