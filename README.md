<p>
  <img src="./resources/images/banner.png" alt="Teachart banner cool" align="center">
</p>
<br clear="left" />
<p align="center">
  <a style="text-decoration:none" href="https://github.com/DeatorFM/Teachart/actions/workflows/python-app.yml">
    <img src="https://github.com/DeatorFM/Teachart/actions/workflows/python-app.yml/badge.svg" alt="Teachart Test Status" />
  </a>
  <a style="text-decoration:none" href="https://www.python.org">
    <img src="https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python 3.12" />
  </a>
  <a style="text-decoration:none" href="https://doc.qt.io/qtforpython-6/">
    <img src="https://img.shields.io/badge/Qt-6.11-brightgreen" alt="Qt 6.11" />
  </a>
</p>
<br>
Teachart is a Qt application written in Python for creating lesson plans in a rich table structure that can hold any information you need for the lesson.
The document looks like a typical spreadsheet that can extend by rows and columns but instead of holding numbers, formulas and plain text it can hold rich text, images and even audio files. Furthermore, teachers can organise  courses and students as well as save schedules to their lesson plans.
This application is currently running only on Windows.

## Background
As a former language teacher, I've always found it a hassle to have multiple windows open for all the materials used in the lesson. At that time, I've thought of an application where I have lesson plan and materials all accessible in one window. Since I was learning Python and experimented with the PyQt library then, I decided to develop an GUI application with this goal in mind. After three years of basically learning the Qt library and different programminbg concepts I published the first version (B1.0.0).

## Features
* Create an extendable table chart where each cell can hold multiple text blocks, images or audio tracks
* Organise you courses and students and keep the information in a portable database file
* Present the contents in your table on a separate screen like you are used from various presentatiom programs
* Save a schedule of for your lesson plan and see all your upcoming lesson on startup
* Light and Dark theme adopted from PyQtDarkTheme by 5yutan

## Building
_This application can be build currently on Windows only_<br>
Make sure to have at least Python 3.12 installed. Clone the repository using `git clone https://github.com/DeatorFM/Teachart.git`. <br>
Inside the project folder, install all dependencies and build with `pip install . --group build` (uv: `uv sync --group build`). <br>
You can now run the application from the terminal by entering `teachart` (uv: `uv run teachart`).
* **Onefile executable using PyInstaller:** Run `ninja build build-dist` after installing dependencies. Alternatively you can download the current version from the releases.

## Screenshots
![Editor in Light mode](https://github.com/DeatorFM/Teachart/blob/main/resources/images/Example1.png)
![Editor in Dark mode](https://github.com/DeatorFM/Teachart/blob/main/resources/images/Example2.png)
![Editing in close up](https://github.com/DeatorFM/Teachart/blob/main/resources/images/Example3.png)
![Course manager](https://github.com/DeatorFM/Teachart/blob/main/resources/images/Example4.png)
