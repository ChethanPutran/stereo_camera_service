# Stereo Camera Service 📷🔧

A Python package to interface a Raspberry Pi with the [Waveshare Binocular Camera Base Board](https://www.waveshare.com/cm4-dual-camera-base.html), enabling stereo image capture and remote access to stereo vision services from a client PC.

---

## 🔧 Features

- Capture stereo image pairs (left and right)
- Live recording
- Live Stream stereo video to a client over sockets
- Modular client-server architecture
- Easily extendable for ROS2 integration or AI vision modules

---

## 🧠 Architecture

```
[Raspberry Pi]
  ├── Waveshare Binocular Camera
  ├── Socket Server (server/camera_server.py)
  └── Image Capture & Streamer
         ↑
[Client PC]
  └── Socket Client (client/camera_client.py)
```

---

## 🚀 Getting Started

### 📦 Installation

1. **Clone the repo**

```bash
git clone https://github.com/ChethanPutran/stereo_camera_service.git
cd stereo_camera_service
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Install the package**

```bash
pip install .
```

---

## 🖥️ Running the Server (on Raspberry Pi)

Make sure the Waveshare Binocular Camera is connected and accessible.
Configure the camera according to Ref: https://www.waveshare.com/wiki/CM4-DUAL-CAMERA-BASE.

Then run:

```bash
python server/camera_server.py
```

This will start a socket server at port `8000`.

---

## 💻 Using the Client (on PC)

You can request stereo images from the client using:

```bash
python client/camera_client.py 
```

More options can be added to save images, display output, or retrieve depth data.

---

## 🧰 Project Structure

```
stereo_camera_service/
├── camera/             # Camera handling and utilities
│   └── camera.py
├── server/             # Socket server code
│   └── camera_server.py
├── client/             # PC-side client to receive images
│   └── camera_client.py
├── requirements.txt
├── setup.py
└── README.md
```

---

## 📌 TODO

- [ ] Add depth estimation using stereo matching
- [ ] Implement image saving feature
- [ ] ROS2 wrapper node
- [ ] MJPEG stream via HTTP/WebSocket
- [ ] Add logging and configuration options

---

## 📄 License

MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Author

**Chethan Putran**  
[GitHub: @ChethanPutran](https://github.com/ChethanPutran)

---

## 🌐 Contributions Welcome!

Feel free to open issues or submit pull requests for improvements, bug fixes, or feature additions.
