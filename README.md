# audio-recording-firmware-raspi-tlv320adc6140
Custom device tree overlay and python firmware control script for the 4 channel ADC tlv320adc6140.  Allows a raspberry pi to create continuous audio recordings.

Example recordings: https://freesound.org/people/filipmu/sounds/591464/, https://freesound.org/people/filipmu/sounds/591463/


For hardware design, including ADC PC board - see https://hackaday.io/project/179489-high-performance-audio-adc-for-machine-learning
For audio classification using deep learning related to this project see https://github.com/filipmu/nature-audio-ai


script autorecord.py depends on:

```
sudo apt install opus-tools
sudo apt install vorbis-tools
sudo apt-get install flac
pip install mutagen
pip install PyAudio
pip install numpy
```

For detailed instructions - see [Raspberry pi recorder.md](Raspberry%20pi%20recorder.md)
