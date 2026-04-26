# Gesture Explorer 
Gesture Explorer is a hands-free file management system that replaces traditional mouse-and-keyboard navigation with intuitive AI-powered hand gestures. Built during BearHacks 2026, this project aims to "break the norm" of digital workspace interaction.

- Inspiration
Standard file navigation is functional but often repetitive. Inspired by the hackathon theme of reinventing the wheel, we set out to create a tool that makes directory manipulation as simple as a wave of a hand.

- Features
Gesture-Based Commands: Use upper body and hand movements to execute commands like Create Folder, Delete Folder, and more.

Streamlined UI: A clean, Windows-inspired environment focused strictly on essential directory manipulation.

Modular "Ball and Socket" Architecture: A flexible backend designed to receive real-time string outputs from an AI model and translate them into immediate file system actions.

- Tech Stack
Language: Python

AI Model: KIMI K2.6 (Transitioned from Google Cloud Vision for better customizability)

API Integration: Custom dataset refinement for gesture recognition.

- How it Works
We utilized a "Ball and Socket" methodology:

The Socket: A Python-based file management environment built to listen for specific string inputs (e.g., "Points_Left").

The Ball: The KIMI K2.6 AI model, trained on custom datasets to recognize movements and output the corresponding string to the "Socket."

- Challenges & Learning
AI Training: We learned that training a model is a meticulous process of selection and refinement, rather than just data feeding.

Pivot to Python: Initially planned as a Chrome extension, we moved to a dedicated Python environment to ensure better scope management and stability.

Version Control: Solidified our collaborative workflow using Git and effective time management under a 24-hour crunch.

- What's Next
Biometric Locks: Implementing gesture-based "passkeys" to encrypt and lock specific folders.

Custom Gestures: Allowing users to record their own movements (like a "bow and arrow" stance) to trigger specific file functions.

Audio Integration: Using ElevenLabs to incorporate sound frequencies as a multi-factor authentication layer.

- Team
Built with heart and character at BearHacks 2026.
