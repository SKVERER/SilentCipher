import streamlit as st
from scipy.io import wavfile
from datetime import datetime
import numpy as np
import tempfile

def encrypt(input_wav, message):
    sample_rate, data = wavfile.read(input_wav)
    if len(data.shape) > 1:
        data = data[:, 0]
    data = data.astype(np.float32)
    time_array = np.arange(len(data)) / sample_rate

    month = datetime.now().month
    day = datetime.now().day
    step = month * day * 100

    for i, char in enumerate(message):
        index = i * step
        if index >= len(data):
            break
        ascii_val = ord(char)
        seconds = int(time_array[index]) % 60
        data[index] = ascii_val - seconds

    data = np.clip(data, -32768, 32767).astype(np.int16)
    return sample_rate, data

def decrypt(input_wav):
    sample_rate, data = wavfile.read(input_wav)
    if len(data.shape) > 1:
        data = data[:, 0]
    data = data.astype(np.float32)
    time_array = np.arange(len(data)) / sample_rate

    month = datetime.now().month
    day = datetime.now().day
    step = month * day * 100

    message = ""
    for index in range(0, len(data), step):
        seconds = int(time_array[index]) % 60
        ascii_val = round(data[index] + seconds)
        if 32 <= ascii_val <= 126:
            message += chr(ascii_val)
        else:
            break
    return message

st.title("🔐 Audio Message Cipher")

mode = st.radio("Choose mode:", ["Encrypt", "Decrypt"])

uploaded_file = st.file_uploader("Upload WAV file", type=["wav"])

if mode == "Encrypt":
    msg = st.text_input("Enter message to encrypt")
    if uploaded_file and msg:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_input:
            temp_input.write(uploaded_file.read())
            sample_rate, encrypted_data = encrypt(temp_input.name, msg)
            temp_output_path = temp_input.name.replace(".wav", "_encrypted.wav")
            wavfile.write(temp_output_path, sample_rate, encrypted_data)
            with open(temp_output_path, "rb") as f:
                st.download_button("Download encrypted file", f, file_name="encrypted.wav")
elif mode == "Decrypt":
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_input:
            temp_input.write(uploaded_file.read())
            message = decrypt(temp_input.name)
            st.success(f"Decrypted Message: {message}")
