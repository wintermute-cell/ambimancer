# Ambimancer
Ambimancer is a program to create, manage and play athmospheric soundscapes, consisting of music and soundeffects.

## Structure
The program consists of two parts:
A server with a graphical interface, that is used for creating and managing files and soundscapes, and managing client connections / sending the required data.

A client with minimal required user interaction capabilities, that receives soundfiles or commands from the server, and plays the transmitted soundscapes. The commands can be sent from the server to control client behaviour such as playback volume.

## Implementation
Multithreading is done using the `threading` library.

The networking is implemented using the `socket` library. Files are split into `packets` of configurable size, to which `target-flags` are appended, to specify whether the packet contains audio data or a command.

The server GUI is done using the `tkinter` library. The client only uses basic python console input, as no more interaction is required.

The layered audio playback is done using the `vlc` library.

## Future goals
Implement all required features, "finishing" the program.
After finalizing the python implementation, reimplement the same functinality in C.
