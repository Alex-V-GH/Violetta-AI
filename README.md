Violetta AI

Overview

Violetta AI is a local Python assistant that combines keyboard input, voice recognition, command execution, and conversational interaction.
It runs entirely on the local machine and uses optional language models for command interpretation and chat.
The system is designed as a modular assistant with concurrent input sources and a central decision loop.

Architecture
Main components:
Violetta – system controller and decision engine
Azul – command execution and command learning
Rosa – conversational response engine
Listener – speech-to-text input
Speaker – text-to-speech output (planned)

Project Goal
Create a fully local, extensible personal assistant capable of:
executing system commands
learning new commands
handling voice input
supporting conversational interaction

running without cloud services
