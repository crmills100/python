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

1. Install Stable Diffussion and AUTOMATIC1111 locally.
2. Configure the URL to webui.sd in config.json



# Running:


1. Start AUTOMATIC1111:
	C:\opt\sd.webui> .\run.bat

	Configuration in webui/webui-user.bat (IP address)
		Noteable options: 
			set COMMANDLINE_ARGS=--lowram --api --server-name=192.168.1.13
			set CUDA_VISIBLE_DEVICES=0

	Configuration options in webui/modules/cmd_args.py

2. Create assets that describe the video to create (see doc/promo_instructions.md)

3. Generate a video for a song on localhost:
	Start the virtualenv:
		pipenv shell
	Run the generator:
		python .\create_image_sequence.py
	

# Caveats

I've only run this on a limited amount of hardware (client running on a Windows 10 host with Stable Diffusion running on a Windows 11 host with a RTX 30 series GPU). As a result, there are likely a few references
to directories that may not exist and are certainly not platform agnostic. If you fix these please send a patch.
