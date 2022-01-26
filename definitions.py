import os.path

# the projects root directory.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# the time (in seconds) between each tich of the ambience emitter.
EMITTER_TICK = 1

# file extensions allowed for upload.
AUDIO_UPLOAD_EXTENSIONS = ['.ogg', '.mp3', '.wav']
IMAGE_UPLOAD_EXTENSIONS = ['.jpg', '.png', '.gif']
