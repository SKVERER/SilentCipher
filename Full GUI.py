import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import numpy as np
import av
from scipy.io import wavfile
from datetime import datetime
import tempfile
from io import BytesIO

st.set_page_config(page_title="🔊 הצפנת מסר בקול", layout="centered")

# כותרת
st.title("🔐 הצפנת מסר בקובץ קול")
st.write("העלה או הקלט קובץ קול, כתוב מסר שתרצה להצפין, והמערכת תצפין אותו בקובץ קול בפורמט WAV.")

# מפתח הצפנה
key = st.number_input("🔢 מפתח הצפנה (ברירת מחדל: 300)", min_value=100, max_value=9999, value=300)

# הקלטה
st.subheader("🎤 הקלט קובץ קול (אופציונלי)")
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_buffer = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.audio_buffer.append(audio)
        return frame

webrtc_ctx = webrtc_streamer(
    key="recorder",
    mode="sendonly",
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

recorded_audio = None
if webrtc_ctx.audio_processor and st.button("💾 שמור הקלטה"):
    st.success("✔️ הקלטה נשמרה!")
    audio_data = np.concatenate(webrtc_ctx.audio_processor.audio_buffer, axis=1).flatten().astype(np.int16)
    recorded_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wavfile.write(recorded_audio.name, 48000, audio_data)
    st.audio(recorded_audio.name)

# או העלאת קובץ
st.subheader("📁 או העלה קובץ קול קיים (WAV בלבד)")
uploaded_file = st.file_uploader("בחר קובץ WAV", type=["wav"])

# טקסט להצפנה
message = st.text_input("💬 הקלד את המסר להצפנה")

# כפתור הצפנה
if st.button("🚀 הצפן ושלח"):
    if not message:
        st.warning("אנא כתוב מסר להצפנה.")
    else:
        if recorded_audio:
            sample_rate, data = wavfile.read(recorded_audio.name)
        elif uploaded_file:
            sample_rate, data = wavfile.read(BytesIO(uploaded_file.read()))
        else:
            st.error("יש להקליט או להעלות קובץ קול.")
            st.stop()

        if len(data.shape) > 1:
            data = data[:, 0]

        data = data.astype(np.float32)
        time_array = np.arange(len(data)) / sample_rate
        month = datetime.now().month
        day = datetime.now().day
        step = month * day * key

        for i, char in enumerate(message):
            index = i * step
            if index >= len(data):
                break
            ascii_val = ord(char)
            seconds = int(time_array[index]) % 60
            new_amplitude = ascii_val - seconds
            data[index] = new_amplitude

        data = np.clip(data, -32768, 32767).astype(np.int16)

        output_buffer = BytesIO()
        wavfile.write(output_buffer, sample_rate, data)
        st.success("🎉 ההצפנה הושלמה!")

        st.download_button(
            label="📥 הורד קובץ מוצפן",
            data=output_buffer.getvalue(),
            file_name="output_encrypted.wav",
            mime="audio/wav"
        )

# פענוח
st.subheader("🕵️‍♂️ פענוח מסר מקובץ קול")

decrypt_file = st.file_uploader("📂 העלה קובץ מוצפן (WAV)", type=["wav"], key="decrypt")

if decrypt_file and st.button("🔍 פענח"):
    sample_rate, data = wavfile.read(BytesIO(decrypt_file.read()))
    if len(data.shape) > 1:
        data = data[:, 0]

    data = data.astype(np.float32)
    time_array = np.arange(len(data)) / sample_rate
    month = datetime.now().month
    day = datetime.now().day
    step = month * day * key

    message = ""
    for index in range(0, len(data), step):
        seconds = int(time_array[index]) % 60
        amplitude = data[index]
        ascii_val = round(amplitude + seconds)

        if 32 <= ascii_val <= 126:
            message += chr(ascii_val)
        else:
            break

    st.success("🔓 המסר המפוענח:")
    st.code(message, language="text")
