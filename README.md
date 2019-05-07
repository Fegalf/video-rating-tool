Author : Nicolas Beaudoin-Gagnon

# About
This tool displays a video that can be rated (binary, 0 or 1) using a keybord "space" key. The program records the rating as a CSV file using the video name and appending "_rating.csv" to it (e.g. test_video.mp4 ---> test_video_rating.csv). Be aware that if an existing file has the same name, it will be overwritten. The program was tested for Windows 10 only.

# Installation
## Installing VLC and Anaconda
1. Download and install VLC at: https://get.videolan.org/vlc/3.0.6/win32/vlc-3.0.6-win32.exe
2. Download and install Anaconda for python 3.7 at: https://www.anaconda.com/distribution/
3. When installation of anaconda is completed, open an Anaconda prompt (look for "anaconda prompt" in windows search bar). This will open a command line interface (CLI). 
4. Download this project as a zip file, and unzip it.

## Setting up and activate the conda environnement 
1. Using the CLI, navigate to the unziped project. 
2. In the project, run this command inside the CLI  ```conda env create -f ratingtoolenv.yml```. This will create an environment (named ```ratingtool```) with all the required dependencies. 
3. Activate the environment using the command ```conda activate ratingtool```. 

# Using the tool
1. To use the rating tool, run the command ```python path/to/main.py```. If you're still inside the project folder, you can simply run 
```python main.py```
2. This will open a small red GUI, which you can use to set rating speed and select the video you want to rate.
3. To start rating, press "Enter".
4. While the video is displayed, use the "Spacebar" key to change the value of rating from 0 to 1. 
5. You can escape at anytime using the "Escape" key. 
6. When the video is over, the program will close itself.

# Collecting rating results
The results are stored in a CSV file, in the same folder as the rated video. Units of time are in miliseconds. 
N.B. The length of the resulting CSV file always match the length of the video. If you quit the program before the video has ended, the results CSV file will be padded with zeros to fit the video length. 

Enjoy! :) 
