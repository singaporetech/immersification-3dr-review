# Enabling Collaborative Scene Authoring with Progressive 3D Reconstruction: A Review of Existing 3D Reconstruction Methods

This repository contains the scripts and documents for the paper.

## Scripts

The Python script used to search, retrieve, and filter papers from PapersWithCode, along with the data dump of the papers

## Dockerfiles

The docker containers are used to review the code from the reviewed papers.

### Install Docker and Nvidia tools:
[Docker](https://docs.docker.com/get-docker/)

[NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) (need to restart the Docker daemon after installing this toolkit)

### Build docker images
- Use the following command line to build the image:

go to the `dockerfiles` directory:
```
cd dockerfiles
```
build the image:
```
docker build -f [dockerfile name] -t [image tag] .
```
For example, to build the image for DeepV2D:
```
docker build -f dockerfile-deepv2d-tf1.12-cuda9.0 -t deepv2d-tf1.12-cuda9.0 .
```
- Use the prebuilt docker images on:

https://hub.docker.com/r/immersification/3dr-review

### Run docker containers
- with terminal only:
```
docker run --gpus all -it --name [container name] [image name]
```
- with terminal and VNC (for desktop environments):
```
docker run --gpus all -it -p [port]:5901 --name [container name] [image name]
```
- with terminal, VNC and bind mounts:
all prebuilt images contain example datasets if they are available. If custom datasets need to be used, create and mount the `datasets` directory to the container.

create the directory:
```
mkdir datasets
```
go to the directory:
```
cd datasets
```
run the container:
```
docker run --gpus all -it -p [port]:5901 --mount type=bind,source="$(pwd)",target=/home/cfi/datasets --name [container name] [image name]
```
For example, if the prebuilt image for DeepV2D is used, the command line will be :
```
docker run --gpus all -dit -p 5901:5901 --mount type=bind,source="$(pwd)",target=/home/cfi/datasets --name deepv2d immersification/democonstruct:deepv2d-tf1.12-cuda9.0
```

### Use desktop environments (optional, but running some code from the reviewed papers may require GUIs)
- install [TigerVNC](https://tigervnc.org/) or other VNC viewers
- and start the viewer
- connect to the VNC server with a port `:1` (if the container is running with the flag `-p 5901:5901`)
- use the container with the xfce4 desktop environment just like a linux system

### Test with example datasets
The example datasets are pre-downloaded (if they are available). Follow the documentations from the relevant repositions to run the demos.

## Repository hierarchy

```
./
├── dockerfiles
│   ├── dockerfile-deeptam-tf1.4-cuda8.0
│   ├── dockerfile-deepv2d-tf1.12-cuda9.0
│   ├── dockerfile-oqm-kinetic-cuda11.3
│   ├── dockerfile-oqm-melodic-cuda11.8
│   ├── dockerfile-oqm-noetic-cuda11.8
│   ├── dockerfile-tandem-cuda11.1-cudnn8
│   └── entrypoint.sh
├── README.md
└── scripts
    └── papers-with-code
        ├── 2023-08-14 01_25_50
        │   ├── discard_list_2.txt
        │   ├── discard_list_3.txt
        │   ├── discard_list_4.txt
        │   ├── discard_list_5.txt
        │   ├── log.txt
        │   ├── papers_list_1.txt
        │   ├── papers_list_2.txt
        │   ├── papers_list_3.txt
        │   ├── papers_list_4.txt
        │   └── papers_list_5.txt
        ├── 2023-08-14 01_33_47
        │   ├── discard_list_2.txt
        │   ├── discard_list_3.txt
        │   ├── discard_list_4.txt
        │   ├── discard_list_5.txt
        │   ├── log.txt
        │   ├── papers_list_1.txt
        │   ├── papers_list_2.txt
        │   ├── papers_list_3.txt
        │   ├── papers_list_4.txt
        │   └── papers_list_5.txt
        └── retrieve_papers_pwc.py

6 directories, 29 files
```