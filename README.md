<div align="center">
<img src="https://i.giphy.com/bGgsc5mWoryfgKBx1u.webp" alt="AI GIF" width="200"/>
</div>
<div align="center">

# EGen-01
 
</div>

**The EGen-01 project aims to develop a highly advanced next-generation artificial intelligence (AI) personal assistant. This system is designed to provide users with unparalleled levels of support and efficiency in their daily lives.**

<div align="center">

## Key Features
</div>

- **Highly Contextual Understanding**: EGen-01 utilizes sophisticated natural language processing (NLP) capabilities to understand user requests and adapt to individual preferences.
- **Proactive Assistance**: The AI assistant actively seeks to anticipate and resolve problems, ensuring seamless productivity and reduced stress levels.
- **Multi-Domain Expertise**: EGen-01 has been engineered to provide expert-level knowledge in a wide range of subjects, making it an invaluable resource for users seeking information or guidance.


<div align="center">

## 🛠 Language and Tools

 ![FastAPI](https://img.shields.io/badge/Fast%20API-%23009688?style=for-the-badge&logo=fastapi&logoColor=white)
 ![Gunicorn](https://img.shields.io/badge/Gunicorn-%23499848?style=for-the-badge&logo=gunicorn&logoColor=white)
 ![LangChain](https://img.shields.io/badge/LangChain-%231C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
 ![OpenAI](https://img.shields.io/badge/OpenAI-%23412991?style=for-the-badge&logo=openai&logoColor=white)
 ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
</div>


## 🛠️ Installation

### Requirements
#### Python 3.12.6 for : ####
- [**Windows** ](https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe)
- [**MacOs** ](https://www.python.org/ftp/python/3.12.7/python-3.12.7-macos11.pkg)
- **Linux Version Update**:

```bash
python3 --version
```

```bash
sudo apt update && sudo apt upgrade -y
```
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
```
```bash
sudo apt update
```
```bash
apt list | grep python3.12
```
<div align="center">
<img src="https://cloudbytes.dev/images/99999980-apt_list.png" alt="AI GIF" width=""/>


if you see somthing like this output you can install python 3.12
</div>

```bash
sudo apt install python3.12
```


### Install Python using MiniConda

1. Download and install MiniConda from [here](https://docs.anaconda.com/miniconda/#quick-command-line-install)
2. Create a new environment using the following command:

   ```bash
   conda create -n EGen-01 python=3.12.6
   ```

3. Activate the environment:

   ```bash
   conda activate EGen-01
   ```

### (Optional) Setup Command Line Interface for Better Readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

### Installation

#### Install the required packages:

```bash
pip install -r requirements.txt
```

#### Setup the environment variables:

```bash
cp .env.example .env
```

Set your environment variables in the `.env` file Example : `OPENAI_API_KEY=your_key`

### Run the FastAPI server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```


<div align="center">

## 🔥 My Stats

[![GitHub Streak](https://github-readme-streak-stats.herokuapp.com?user=EGen&theme=dark&hide_border=true&date_format=M%20j%5B%2C%20Y%5D)](https://git.io/streak-stats)



## Contact us
![ErebusTN](https://img.shields.io/badge/ErebusTN-%20?style=for-the-badge&logo=devdotto&logoColor=%23faf9f8&label=Dev%20%3A%20&color=%238b0000)
![Static Badge](https://img.shields.io/badge/The%20Underworld%20server-%20?style=for-the-badge&logo=discord&logoColor=%23faf9f8&logoSize=auto&color=%235865F2&link=https%3A%2F%2Fgithub.com%2FErebusTN)

## Note 
This is my first project and my first experience working with this technology. I'm excited to learn and grow as a developer, and any feedback or contributions to help improve this project are greatly appreciated.

Thank you in advance for your support and guidance!
</div>
