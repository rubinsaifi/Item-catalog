# Item-Catalog Project (Udacity Nanodegree - Full Stack Web Developer)

## Requirements
Develop Item Catalog application that provides a list of items within a variety of categories, as well as provide a user registration and authentication system. 


## System Requirement and Prerequisites
- Python3.x
- *NIX Machine (Vagrant+Virtualbox+FullStackVM or BareMetal Unix/Linux/MacOS)

## Steps to run project
1. Download and Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads) and [Vagrant](https://www.vagrantup.com/downloads.html) (if not using base OS).
2. Clone/Download Vagrant VM configuration provided by [Udacity](https://github.com/udacity/fullstack-nanodegree-vm) (if not using base OS)
3. In Case of Vagrant VM, go to vagrant config location and perform following actions:
```vagrant up
vagrant ssh
cd /vagrant/
git clone https://github.com/rubinsaifi/Item-catalog.git
```

In case using BareMetal machine, go to project folder
4. Install Python packages
```pip install -r requirements.txt```
5. Setup SQLite DB
```python database_setup.py```
6. Add Initial Items to SQLite DB
```python fake_item_populator.py```
7. Signup for Google oAuth and update following values in client_secrets.json:
```
"client_id": "SIGNUP-FOR-CLIENT-ID,
"project_id": "PROJECT-ID",
"client_secret": "CLIENT-SECRET",
```

8. Run Python Application
```python app.py````
9. Open `http://localhost:5000/' in Browser-of-Choice

## Feature Request and Bugs
This project is a part of Nanodegree although you can sent pull requests by forking this project

## Licence
MIT License

Copyright (c) [2019] [Rubin Saifi]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Credits and Special Thanks
[Udacity](https://udacity.com) Team for making this amazing course
