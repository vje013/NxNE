import os

file_path = '/Users/MacBook/Desktop/NxNE/tagline_generator/templates/waitlist.html'

if os.path.isfile(file_path):
    print("File is accessible")
else:
    print("File is not accessible")


