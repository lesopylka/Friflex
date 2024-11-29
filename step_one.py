import streamlit as st
import os
from openai import OpenAI
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_audioclips, ImageClip
import re
from datetime import timedelta
import json
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_audioclips, TextClip, concatenate_videoclips
from pathlib import Path
from moviepy.video.tools.subtitles import SubtitlesClip
from openai import OpenAI
import requests


# Функция для загрузки файла в указанную папку
def upload_file(file, folder):
    # Создаем указанную папку, если ее нет
    os.makedirs(folder, exist_ok=True)
    # Очищаем папку, если она не пуста
    files_in_folder = os.listdir(folder)
    for file_in_folder in files_in_folder:
        os.remove(os.path.join(folder, file_in_folder))
    # Сохраняем загруженный файл в указанную папку
    with open(os.path.join(folder, file.name), "wb") as f:
        f.write(file.getbuffer())


def gpt_processing(cont):

    # api_key = "sk-4vuoCnm0s21wVTOeJOu3etVwrMGDicV8"
    # client = OpenAI(api_key=api_key, base_url="https://api.proxyapi.ru/openai/v1")

    api_key = "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"
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    response_format={ "type": "json_object" },
    temperature=0.3,
    messages=[
        {"role": "system", "content": "Ты самый лучший эксперт по шахматам и аналитик партий. Найди самый интересный ход в партии. \
        Опиши его максимально подробно для людей, которые ничего не понимают в шахматах на 20-30 секунд чтения. Ходы игры хранятся в pgn формате.  \
        Пиши на русском. \
        Выведи json файл с временной меткой интересного хода (ключ timestamp) и коментарием к этому моменту (ключ comment)."},

        {"role": "user", "content": cont}
    ]
    )
    # # Parse JSON
    data = json.loads(response.choices[0].message.content)

    # Extract variables
    timestamp = data['timestamp']
    comment = data['comment']
    print("Timestamp:", timestamp)
    print("Comment:", comment)
    return(timestamp, comment)



def read_pgn(pgn_file_path):
    def read_pgn_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.readlines()

    def write_selected_lines_to_list(pgn_lines):
        selected_lines = []
        for i in range(12, len(pgn_lines), 14):
            selected_lines.append(pgn_lines[i])
        return selected_lines

    pgn_lines = read_pgn_file(pgn_file_path)
    return write_selected_lines_to_list(pgn_lines)


def audio(video_path, static_text):
    #music_path = '/content/drive/MyDrive/Cream_Soda_-_Plachu_na_tehno.mp3'
    audio_output_path = 'gpt_speech.mp3'
    final_video_path = 'mp4_folder/final_output.mp4'
    text_image_path = 'text_image.png'

    # Создание директории, если она не существует
    # os.makedirs(os.path.dirname(audio_output_path), exist_ok=True)

    # Текст для озвучивания и отображения на видео
    
    # Генерация аудио из текста
    # client = OpenAI(api_key='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')

    #speech_file_path = Path(audio_output_path).parent / audio_output_path

    # Define constants for the script
    CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
    XI_API_KEY = "fcafbaec6df8d8787f4f004b8d0753c7"  # Your API key for authentication
    VOICE_ID = "QXSqZPfDRMcd2d8C0Jgj"  # ID of the voice model to use
    # Construct the URL for the Text-to-Speech API request
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

    # Set up headers for the API request, including the API key for authentication
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }

    # Set up the data payload for the API request, including the text and voice settings
    data = {
        "text": static_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    # Make the POST request to the TTS API with headers and data, enabling streaming response
    response = requests.post(tts_url, headers=headers, json=data, stream=True)

    # Check if the request was successful
    if response.ok:
        # Open the output file in write-binary mode
        with open(audio_output_path, "wb") as f:
            # Read the response in chunks and write to the file
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        # Inform the user of success
        print("Audio stream saved successfully.")
    else:
        # Print the error message if the request was not successful
        print(response.text)


    gpt_audio_clip = AudioFileClip(audio_output_path)

    # Define subtitle duration and position
    subtitle_fontsize = 24
    subtitle_font = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
    subtitle_color = 'black'
    subtitle_position = ('center', 'bottom')

    # Function to generate subtitles
    def generate_subtitles(text, start_time, end_time, font_size, font, color):
        return TextClip(text, fontsize=font_size, font=font, color=color).set_start(start_time).set_end(end_time)

    def split_text_with_index(text, segment_length, interval):
        words = text.split()
        segments = []
        start = 0
        end = interval
        for i in range(0, len(words), segment_length):
            segment_text = ' '.join(words[i:i+segment_length])
            # end = min(start + segment_length - 1, len(words) - 1)
            segments.append({"text": segment_text, "start": start, "end": end})
            start = end
            end += interval

        return segments

    subtitle_segments = split_text_with_index(static_text, segment_length=4, interval=2.5)
    subtitles = [
        generate_subtitles(seg["text"], seg["start"], seg["end"], subtitle_fontsize, subtitle_font, subtitle_color)
        for seg in subtitle_segments
    ]

    # Concatenate subtitle clips into a single clip
    subtitles_clip = concatenate_videoclips(subtitles, method="compose")

    # Position subtitle clip
    subtitles_clip = subtitles_clip.set_position(subtitle_position)

    # Загрузка видео и музыкального клипа
    video_clip = VideoFileClip(video_path)
    #music_clip = AudioFileClip(music_path).subclip(0, video_clip.duration)

    # Комбинирование аудио
    #combined_audio = concatenate_audioclips([gpt_audio_clip, music_clip.set_duration(video_clip.duration)])

    # Композитное видео с текстом
    final_video = CompositeVideoClip([video_clip, subtitles_clip.set_start(0)])
    final_video = final_video.set_audio(gpt_audio_clip)

    # Экспорт финального видео
    final_video.write_videofile(final_video_path, codec="libx264")


def cutting(bord1, bord2, video_path):
    tmp1 = "tmp1.mp4"

    command = ['ffmpeg', '-i', video_path, '-ss', str(bord1), '-to', str(bord2), '-c', 'copy', tmp1]
    subprocess.run(command)

    clip = VideoFileClip(tmp1)
    clip = clip.rotate(90, expand=True)
    clip = clip.resize(height=1920)
    output_path = "mp4_folder/shorts.mp4"

    # Save the modified clip to a new file
    clip.write_videofile(output_path, codec="libx264")


def video_proc(min, sec):
        # путь видео
        vf_path = "mp4_folder"
        files = os.listdir(vf_path)
        video_name = files[0]
        video_path = os.path.join(vf_path, video_name)
        # номер партии
        match = re.search(r'\d+', video_name)
        board = int(match.group()) - 1
        # путь п
        pf_path = "pgn_folder"
        files1 = os.listdir(pf_path)
        pgn_name = files1[0]
        pgn_file_path = os.path.join(pf_path, pgn_name)
        # таймстемпы
        lines = read_pgn(pgn_file_path)
        line = lines[board]
        (timestamp, comment) = gpt_processing(line)
        print(comment)
        ts_numbers = re.findall(r'%ts (\d+)', line)
        time1 = min*60 + sec

        def time_change(ms, start, start_ok):
            t =  start_ok + (ms - start) / 1000
            return (t - 10, t + 10)

        (bord1, bord2) = time_change(timestamp, int(ts_numbers[0]), time1)
        print(bord1, bord2)
        #bord1 = 3650
        #bord2 = 3670
        cutting(bord1, bord2, video_path)
        output_path = "mp4_folder/shorts.mp4"
        audio(output_path, comment)



# Главная страница с загрузкой файлов
def main_page():
    st.title('Загрузка файлов')

    # Загружаем файлы формата mp4 и pgn в отдельные папки
    uploaded_mp4_file = st.file_uploader("Выберите файл MP4", type=['mp4'])
    uploaded_pgn_file = st.file_uploader("Выберите файл PGN", type=['pgn'])

    if uploaded_mp4_file is not None:
        upload_file(uploaded_mp4_file, "mp4_folder")
        st.success('MP4 файл успешно загружен!')

    if uploaded_pgn_file is not None:
        upload_file(uploaded_pgn_file, "pgn_folder")
        st.success('PGN файл успешно загружен!')

    minutes = st.number_input("Минуты", min_value=0, step=1, value=None)
    seconds = st.number_input("Секунды", min_value=0, max_value=59, step=1, value=None)

    if st.button("Обработать видео"):
        if uploaded_mp4_file and uploaded_pgn_file and minutes is not None and seconds is not None:
            video_proc(minutes, seconds)
    
    st.markdown("[Просмотр видео](/?page=video)")


# Страница с видео
def video_page():
    st.title('Просмотр видео')

    # Загружаем видео из папки mp4_folder
    mp4_folder = "mp4_folder"
    mp4_files = [os.path.join(mp4_folder, f) for f in os.listdir(mp4_folder) if f.endswith('.mp4')]

    if not mp4_files:
        st.write("В папке MP4 нет видео файлов")
    else:
        # Устанавливаем индекс текущего видео
        video_index = st.session_state.get('video_index', 0)
        # Отображаем текущее видео
        st.video(mp4_files[video_index])

        # Символы стрелок
        left_arrow = u"\u25C0"  # ◄
        right_arrow = u"\u25B6"  # ►

        # Кнопки для перемещения к предыдущему и следующему видео
        col1, col2, col3 = st.columns([1, 10, 1])
        if col1.button(left_arrow, key='prev_video', disabled=video_index == 0):
            st.session_state['video_index'] = max(0, video_index - 1)
        if col3.button(right_arrow, key='next_video', disabled=video_index == len(mp4_files) - 1):
            st.session_state['video_index'] = min(len(mp4_files) - 1, video_index + 1)


# Определяем текущую страницу и вызываем соответствующую функцию
current_page = st.query_params.get("page", "main")
if current_page == "video":
    video_page()
else:
    main_page()
