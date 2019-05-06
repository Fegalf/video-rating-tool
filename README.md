Author : Nicolas Beaudoin-Gagnon

# About
This tool displays a video that can be rated (binary, 0 or 1) using a keybord "space" key. The program records the rating as a CSV file using the video name and appending "_rating.csv" to it (e.g. test_video.mp4 ---> test_video_rating.csv). Be aware that if an existing file has the same name, it will be overwritten. The program was tested for Windows 10 only.

# Installation
## Installing VLC and Anaconda
1. Download and install VLC at: https://get.videolan.org/vlc/3.0.6/win32/vlc-3.0.6-win32.exe
2. Download and install Anaconda for python 3.7 at: https://www.anaconda.com/distribution/
3. When installation of anaconda is completed, open an Anaconda prompt (look for "anaconda prompt" in windows search bar). This will open a command line interface (CLI). 
4. Download this project as a zip file, and unzip it.

## Setting up the conda environnement 
1. Using the CLI, navigate to the unziped project. 
2. In the project, run this command inside the CLI 
```python
conda env create -f environment.yml
```
This will create an environment (named ```python353```) with all the required dependencies. 

3. Activate the environment using the command ```conda activate python353```. 
4. To use the rating tool, run the command ```python main.py```
5. This will open a small GUI, which you can use to set rating speed and select the video you want to rate.
