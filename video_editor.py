import os
import random
from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import imageio_ffmpeg

class VideoEditor:
    def __init__(self, clips_dir="assets/clips"):
        self.clips_dir = clips_dir

    def create_text_image(self, text, size=(1080, 1920), font_size=60, color=(255, 255, 255)):
        """
        Crea una imagen con texto usando PIL como alternativa a ImageMagick.
        """
        # Crear una imagen transparente
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Intentar cargar una fuente, si no, usar la por defecto
        try:
            # En Linux usualmente hay fuentes en /usr/share/fonts
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "assets/fonts/bold.ttf"
            ]
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    font = ImageFont.truetype(path, font_size)
                    break
            if not font:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Ajustar texto (wrapping)
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            # Aproximación simple de ancho de línea
            if len(" ".join(current_line)) * (font_size * 0.6) > size[0] * 0.8:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        lines.append(" ".join(current_line))

        # Dibujar líneas centraras
        y_offset = size[1] // 2 - (len(lines) * font_size) // 2
        for line in lines:
            # Obtener dimensiones del texto
            try:
                left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
                w, h = right - left, bottom - top
            except:
                w, h = len(line) * (font_size * 0.6), font_size

            x = (size[0] - w) // 2
            # Dibujar borde negro para legibilidad
            for adj in range(-2, 3):
                for adj_y in range(-2, 3):
                    draw.text((x+adj, y_offset+adj_y), line, font=font, fill=(0,0,0,255))

            draw.text((x, y_offset), line, font=font, fill=color)
            y_offset += font_size + 10

        return np.array(img)

    def create_video(self, audio_path, output_path, script_text):
        """
        Crea un video Short (9:16) mezclando clips aleatorios con audio y subtítulos.
        """
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        # Obtener clips disponibles
        if not os.path.exists(self.clips_dir):
            os.makedirs(self.clips_dir)

        available_clips = [f for f in os.listdir(self.clips_dir) if f.endswith(('.mp4', '.mov', '.avi'))]

        if not available_clips:
            background = ColorClip(size=(1080, 1920), color=(30, 30, 30)).with_duration(duration)
        else:
            selected_clips = []
            current_duration = 0

            while current_duration < duration:
                clip_name = random.choice(available_clips)
                clip_path = os.path.join(self.clips_dir, clip_name)
                clip = VideoFileClip(clip_path).without_audio()

                # Redimensionar para Short (9:16)
                w, h = clip.size
                target_ratio = 9/16

                if w/h > target_ratio:
                    new_w = h * target_ratio
                    clip = clip.cropped(x_center=w/2, width=new_w)
                else:
                    new_h = w / target_ratio
                    clip = clip.cropped(y_center=h/2, height=new_h)

                clip = clip.resized(width=1080)

                remaining = duration - current_duration
                if clip.duration > remaining:
                    clip = clip.subclipped(0, remaining)

                selected_clips.append(clip)
                current_duration += clip.duration

            from moviepy import concatenate_videoclips
            background = concatenate_videoclips(selected_clips)

        # Añadir audio
        final_video = background.with_audio(audio)

        # Crear subtítulo usando Pillow
        txt_img = self.create_text_image(script_text)
        txt_clip = ImageClip(txt_img).with_duration(duration).with_position(('center', 'center'))

        final_video = CompositeVideoClip([final_video, txt_clip])

        final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        return output_path
