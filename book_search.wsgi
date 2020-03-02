import os, sys

# edit your username below
sys.path.append("/home/geojoe/public_html/book_search");

sys.path.insert(0, os.path.dirname(__file__))
from app import app as application

# make the secret code a little better
application.secret_key = '3B0C0BD9EB1F47A21C057C49550402332E3D31C0DD22B71ED2B69C36DAC8F60AA1508FBEEC75B00C1F9815B95AC611EA71A288BEADF148EEB3E2DBD095616DEB'
