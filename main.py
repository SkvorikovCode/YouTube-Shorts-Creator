#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Shorts Creator
Автоматическое создание коротких роликов из YouTube видео с использованием ИИ

Автор: SkvorikovCode
Год: 2025
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Импорты для работы с видео и ИИ
try:
    import yt_dlp
    import whisper
    import requests
    from colorama import init, Fore, Back, Style
    import ffmpeg
    from tqdm import tqdm
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📦 Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)

# Инициализация colorama для кроссплатформенной поддержки цветов
init(autoreset=True)

class ShortsCreator:
    """Основной класс для создания коротких роликов из YouTube видео"""
    
    def __init__(self, config_path: str = "config.json"):
        """Инициализация с загрузкой конфигурации"""
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.setup_directories()
        self.whisper_model = None
        
        # Статистика обработки
        self.stats = {
            "start_time": datetime.now(),
            "videos_processed": 0,
            "shorts_created": 0,
            "errors": 0
        }
        
        self.logger.info(f"🚀 {self.config['app']['name']} v{self.config['app']['version']} запущен")
    
    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации из JSON файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Файл конфигурации {config_path} не найден")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка в файле конфигурации: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Настройка системы логирования"""
        log_config = self.config['logging']
        
        # Создание форматтера
        formatter = logging.Formatter(log_config['format'])
        
        # Настройка основного логгера
        self.logger = logging.getLogger('ShortsCreator')
        self.logger.setLevel(getattr(logging, log_config['level']))
        
        # Консольный обработчик с цветами
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Файловый обработчик
        if log_config['file_logging']:
            # Убеждаемся, что директория для логов существует
            logs_dir = Path(self.config['paths']['logs_dir'])
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = logs_dir / f"shorts_creator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def setup_directories(self):
        """Создание необходимых директорий"""
        for path_key, path_value in self.config['paths'].items():
            Path(path_value).mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"📁 Создана директория: {path_value}")
    
    def print_banner(self):
        """Вывод баннера приложения"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    YouTube Shorts Creator                    ║
║                   Автор: SkvorikovCode                       ║
║                        Год: 2025                             ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
    
    def download_video(self, input_path: str) -> Optional[Dict]:
        """Скачивание видео с YouTube или обработка локального файла"""
        
        # Проверяем, является ли input_path локальным файлом
        if os.path.exists(input_path):
            return self._process_local_file(input_path)
        
        # Иначе обрабатываем как YouTube URL
        self.logger.info(f"📥 Начинаем скачивание видео: {input_path}")
        url = input_path
        
        # Настройки для yt-dlp
        ydl_opts = {
            'format': f'best[height<={self.config["video"]["video_quality"][:-1]}]',
            'outtmpl': os.path.join(self.config['paths']['temp_dir'], '%(title)s.%(ext)s'),
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ru', 'en'],
            'ignoreerrors': True,
            'cookiesfrombrowser': ('chrome',),  # Используем cookies из Chrome
            'extractor_retries': 3,
            'fragment_retries': 3,
        }
        
        try:
            # Попробуем разные браузеры для cookies
            browsers = [('chrome',), ('firefox',), ('safari',), None]
            
            for browser in browsers:
                try:
                    if browser:
                        ydl_opts['cookiesfrombrowser'] = browser
                        self.logger.info(f"🍪 Пробуем cookies из {browser[0]}")
                    else:
                        ydl_opts.pop('cookiesfrombrowser', None)
                        self.logger.info("🔄 Пробуем без cookies")
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Получение информации о видео
                        info = ydl.extract_info(url, download=False)
                        break  # Если успешно, выходим из цикла
                        
                except Exception as e:
                    if browser:
                        self.logger.warning(f"⚠️ Не удалось использовать cookies из {browser[0]}: {e}")
                    else:
                        self.logger.warning(f"⚠️ Не удалось загрузить без cookies: {e}")
                    if browser == browsers[-1]:  # Если это последняя попытка
                        raise e
                    continue
                
            if not info:
                self.logger.error("❌ Не удалось получить информацию о видео")
                return None
            
            video_info = {
                'id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration'),
                'description': info.get('description'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date')
            }
            
            # Проверка критически важных полей
            if not video_info['duration'] or not video_info['title']:
                self.logger.error("❌ Отсутствует критически важная информация о видео (длительность или название)")
                return None
            
            self.logger.info(f"📺 Видео: {video_info['title']} ({video_info['duration']} сек)")
            
            # Проверка длительности
            if video_info['duration'] < self.config['video']['min_short_duration']:
                self.logger.warning("⚠️ Видео слишком короткое для создания shorts")
                return None
            
            # Скачивание видео с теми же настройками
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # Поиск скачанного файла
            temp_dir = Path(self.config['paths']['temp_dir'])
            
            # Попробуем несколько паттернов поиска
            search_patterns = [
                f"*{video_info['id']}*",
                f"*{video_info['title'][:20]}*" if video_info['title'] else None,
                "*.mp4", "*.webm", "*.mkv", "*.avi"
            ]
            
            video_files = []
            for pattern in search_patterns:
                if pattern:
                    files = list(temp_dir.glob(pattern))
                    if files:
                        video_files = files
                        break
            
            if video_files:
                # Берем самый новый файл
                video_file = max(video_files, key=lambda f: f.stat().st_mtime)
                video_info['file_path'] = str(video_file)
                self.logger.info(f"✅ Видео скачано: {video_info['file_path']}")
                return video_info
            else:
                self.logger.error("❌ Не удалось найти скачанный файл")
                self.logger.debug(f"Искали в директории: {temp_dir}")
                return None
                    
        except Exception as e:
            self.logger.error(f"❌ Ошибка при скачивании видео: {e}")
            self.stats['errors'] += 1
            return None
    
    def _process_local_file(self, file_path: str) -> Optional[Dict]:
        """Обработка локального видеофайла"""
        self.logger.info(f"📁 Обрабатываем локальный файл: {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"❌ Файл не найден: {file_path}")
            return None
        
        # Получаем информацию о видео с помощью ffmpeg
        try:
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                self.logger.error("❌ Видеопоток не найден в файле")
                return None
            
            duration = float(probe['format']['duration'])
            filename = os.path.basename(file_path)
            title = os.path.splitext(filename)[0]
            
            video_info = {
                'id': f"local_{hash(file_path)}",
                'title': title,
                'duration': duration,
                'description': f"Локальный файл: {filename}",
                'uploader': 'Local File',
                'upload_date': None,
                'file_path': file_path
            }
            
            # Проверка критически важных полей
            if not video_info['duration'] or not video_info['title']:
                self.logger.error("❌ Отсутствует критически важная информация о видео")
                return None
            
            self.logger.info(f"📺 Видео: {video_info['title']} ({video_info['duration']:.1f} сек)")
            
            # Проверка длительности
            if video_info['duration'] < self.config['video']['min_short_duration']:
                self.logger.warning("⚠️ Видео слишком короткое для создания shorts")
                return None
            
            return video_info
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при анализе локального файла: {e}")
            return None
    
    def extract_audio_and_subtitles(self, video_info: Dict) -> Dict:
        """Извлечение аудио и субтитров из видео"""
        self.logger.info("🎵 Извлекаем аудио для анализа")
        
        if 'file_path' not in video_info or not video_info['file_path']:
            self.logger.error("❌ Отсутствует путь к видеофайлу")
            return {}
        
        video_path = video_info['file_path']
        
        if not os.path.exists(video_path):
            self.logger.error(f"❌ Видеофайл не найден: {video_path}")
            return {}
        
        audio_path = os.path.join(self.config['paths']['temp_dir'], f"{video_info['id']}_audio.wav")
        
        try:
            # Извлечение аудио с помощью ffmpeg
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(quiet=True)
            )
            
            self.logger.info(f"✅ Аудио извлечено: {audio_path}")
            
            # Транскрипция с помощью Whisper
            if not self.whisper_model:
                self.logger.info("🤖 Загружаем модель Whisper...")
                self.whisper_model = whisper.load_model(self.config['ai']['whisper']['model'])
            
            self.logger.info("📝 Выполняем транскрипцию...")
            result = self.whisper_model.transcribe(audio_path)
            
            return {
                'audio_path': audio_path,
                'transcription': result['text'],
                'segments': result['segments']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при извлечении аудио: {e}")
            self.stats['errors'] += 1
            return {}
    
    def analyze_content_with_ai(self, video_info: Dict, audio_data: Dict) -> List[Dict]:
        """Анализ контента с помощью ИИ для определения лучших моментов"""
        self.logger.info("🧠 Анализируем контент с помощью ИИ...")
        
        # Подготовка данных для анализа
        content_summary = {
            'title': video_info['title'],
            'duration': video_info['duration'],
            'transcription': audio_data.get('transcription', ''),
            'segments': audio_data.get('segments', [])
        }
        
        # Формирование промпта для ИИ
        prompt = self._create_analysis_prompt(content_summary)
        
        try:
            # Запрос к Ollama
            response = self._query_ollama(prompt)
            
            if response:
                # Парсинг ответа ИИ для получения временных меток
                segments = self._parse_ai_response(response, video_info['duration'])
                self.logger.info(f"✅ ИИ предложил {len(segments)} сегментов для shorts")
                return segments
            else:
                # Fallback: равномерное деление
                return self._create_fallback_segments(video_info['duration'])
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка при анализе ИИ: {e}")
            self.stats['errors'] += 1
            return self._create_fallback_segments(video_info['duration'])
    
    def _create_analysis_prompt(self, content: Dict) -> str:
        """Создание промпта для анализа контента"""
        return f"""
Проанализируй следующее видео и определи 3-5 наиболее интересных моментов для создания 60-секундных shorts:

Название: {content['title']}
Длительность: {content['duration']} секунд
Транскрипция: {content['transcription'][:2000]}...

Верни результат в формате JSON со следующей структурой:
{{
  "segments": [
    {{
      "start_time": 0,
      "end_time": 60,
      "description": "Описание сегмента",
      "relevance_score": 0.9
    }}
  ]
}}

Требования:
- Каждый сегмент должен быть от 15 до 60 секунд
- Выбирай самые интересные и законченные по смыслу фрагменты
- Избегай пересечений между сегментами
- Оценивай релевантность от 0 до 1
        """
    
    def _query_ollama(self, prompt: str) -> Optional[str]:
        """Запрос к Ollama API"""
        ollama_config = self.config['ai']['ollama']
        
        try:
            response = requests.post(
                f"{ollama_config['base_url']}/api/generate",
                json={
                    'model': ollama_config['model'],
                    'prompt': prompt,
                    'stream': False
                },
                timeout=ollama_config['timeout']
            )
            
            if response.status_code == 200:
                return response.json().get('response')
            else:
                self.logger.warning(f"⚠️ Ollama вернул код {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            self.logger.warning("⚠️ Не удалось подключиться к Ollama. Убедитесь, что сервис запущен.")
            return None
        except Exception as e:
            self.logger.error(f"❌ Ошибка при запросе к Ollama: {e}")
            return None
    
    def _parse_ai_response(self, response: str, video_duration: int) -> List[Dict]:
        """Парсинг ответа ИИ"""
        try:
            # Попытка извлечь JSON из ответа
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                segments = data.get('segments', [])
                
                # Валидация и фильтрация сегментов
                valid_segments = []
                for segment in segments:
                    if (segment.get('start_time', 0) >= 0 and 
                        segment.get('end_time', 0) <= video_duration and
                        segment.get('end_time', 0) - segment.get('start_time', 0) >= self.config['video']['min_short_duration']):
                        valid_segments.append(segment)
                
                return valid_segments[:5]  # Максимум 5 сегментов
            
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось распарсить ответ ИИ: {e}")
        
        return self._create_fallback_segments(video_duration)
    
    def _create_fallback_segments(self, duration: int) -> List[Dict]:
        """Создание сегментов по умолчанию при ошибке ИИ"""
        self.logger.info("📐 Создаем сегменты равномерным делением")
        
        segment_duration = self.config['video']['max_short_duration']
        segments = []
        duration = int(duration)  # Преобразуем в int для range()
        
        for i in range(0, duration, segment_duration):
            end_time = min(i + segment_duration, duration)
            if end_time - i >= self.config['video']['min_short_duration']:
                segments.append({
                    'start_time': i,
                    'end_time': end_time,
                    'description': f'Сегмент {len(segments) + 1}',
                    'relevance_score': 0.5
                })
        
        return segments
    
    def create_shorts(self, video_info: Dict, segments: List[Dict]) -> List[str]:
        """Создание коротких роликов из сегментов"""
        if not segments:
            self.logger.warning("⚠️ Нет сегментов для создания shorts")
            return []
        
        self.logger.info(f"✂️ Создаем {len(segments)} коротких роликов...")
        
        output_files = []
        
        if 'file_path' not in video_info or not video_info['file_path']:
            self.logger.error("❌ Отсутствует путь к видеофайлу")
            return []
        
        video_path = video_info['file_path']
        
        if not os.path.exists(video_path):
            self.logger.error(f"❌ Видеофайл не найден: {video_path}")
            return []
        
        # Создание папки для выходных файлов
        output_dir = Path(self.config['paths']['output_dir']) / self._sanitize_filename(video_info['title'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, segment in enumerate(tqdm(segments, desc="Создание shorts")):
            try:
                # Проверка корректности данных сегмента
                if not isinstance(segment, dict) or 'start_time' not in segment or 'end_time' not in segment:
                    self.logger.error(f"❌ Некорректные данные сегмента {i+1}")
                    self.stats['errors'] += 1
                    continue
                
                start_time = segment['start_time']
                end_time = segment['end_time']
                
                if start_time >= end_time or start_time < 0:
                    self.logger.error(f"❌ Некорректное время сегмента {i+1}: {start_time}-{end_time}")
                    self.stats['errors'] += 1
                    continue
                
                output_file = output_dir / f"short_{i+1:03d}.mp4"
                
                # Нарезка видео с помощью ffmpeg
                (
                    ffmpeg
                    .input(video_path, ss=start_time, t=end_time - start_time)
                    .output(
                        str(output_file),
                        vcodec='libx264',
                        acodec='aac',
                        **{'crf': '23', 'preset': 'medium'}
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                output_files.append(str(output_file))
                self.logger.info(f"✅ Создан short: {output_file.name}")
                self.stats['shorts_created'] += 1
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка при создании short {i+1}: {e}")
                self.stats['errors'] += 1
        
        return output_files
    
    def generate_metadata(self, video_info: Dict, segments: List[Dict], output_files: List[str]):
        """Генерация метаданных для созданных shorts"""
        self.logger.info("📋 Генерируем метаданные для shorts...")
        
        metadata_dir = Path(self.config['paths']['output_dir']) / self._sanitize_filename(video_info['title']) / 'metadata'
        metadata_dir.mkdir(exist_ok=True)
        
        for i, (segment, output_file) in enumerate(zip(segments, output_files)):
            try:
                # Генерация названия и описания через ИИ
                title, description = self._generate_short_metadata(video_info, segment)
                
                metadata = {
                    'original_video': {
                        'title': video_info['title'],
                        'url': video_info.get('url', ''),
                        'duration': video_info['duration']
                    },
                    'short': {
                        'file_path': output_file,
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time'],
                        'duration': segment['end_time'] - segment['start_time'],
                        'title': title,
                        'description': description,
                        'relevance_score': segment.get('relevance_score', 0.5)
                    },
                    'generated_at': datetime.now().isoformat(),
                    'generator': f"{self.config['app']['name']} v{self.config['app']['version']}"
                }
                
                metadata_file = metadata_dir / f"short_{i+1:03d}_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                self.logger.debug(f"📄 Метаданные сохранены: {metadata_file.name}")
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка при генерации метаданных для short {i+1}: {e}")
    
    def _generate_short_metadata(self, video_info: Dict, segment: Dict) -> Tuple[str, str]:
        """Генерация названия и описания для short через ИИ"""
        if not self.config['features']['auto_generate_titles']:
            return f"Short из {video_info['title']}", segment.get('description', '')
        
        prompt = f"""
Создай привлекательное название и описание для короткого ролика:

Исходное видео: {video_info['title']}
Фрагмент: {segment.get('description', '')}
Время: {segment['start_time']}-{segment['end_time']} сек

Верни результат в формате:
Название: [короткое цепляющее название]
Описание: [краткое описание до 100 символов]
        """
        
        try:
            response = self._query_ollama(prompt)
            if response:
                lines = response.strip().split('\n')
                title = "Short из " + video_info['title'][:30]
                description = segment.get('description', '')
                
                for line in lines:
                    if line.startswith('Название:'):
                        title = line.replace('Название:', '').strip()
                    elif line.startswith('Описание:'):
                        description = line.replace('Описание:', '').strip()
                
                return title, description
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка при генерации метаданных: {e}")
        
        return f"Short из {video_info['title'][:30]}", segment.get('description', '')
    
    def _sanitize_filename(self, filename: str) -> str:
        """Очистка имени файла от недопустимых символов"""
        import re
        return re.sub(r'[<>:"/\\|?*]', '_', filename)[:50]
    
    def cleanup_temp_files(self):
        """Очистка временных файлов"""
        if not self.config['processing']['preserve_temp_files']:
            temp_dir = Path(self.config['paths']['temp_dir'])
            for file in temp_dir.glob('*'):
                try:
                    file.unlink()
                    self.logger.debug(f"🗑️ Удален временный файл: {file.name}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Не удалось удалить {file.name}: {e}")
    
    def print_statistics(self):
        """Вывод статистики обработки"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        
        print(f"\n{Fore.GREEN}📊 Статистика обработки:{Style.RESET_ALL}")
        print(f"⏱️ Время выполнения: {duration}")
        print(f"📹 Обработано видео: {self.stats['videos_processed']}")
        print(f"✂️ Создано shorts: {self.stats['shorts_created']}")
        print(f"❌ Ошибок: {self.stats['errors']}")
        
        if self.stats['shorts_created'] > 0:
            print(f"\n{Fore.CYAN}🎉 Shorts успешно созданы! Проверьте папку: {self.config['paths']['output_dir']}{Style.RESET_ALL}")
    
    def process_video(self, url: str) -> bool:
        """Основной метод обработки видео"""
        try:
            # 1. Скачивание видео
            video_info = self.download_video(url)
            if not video_info:
                return False
            
            video_info['url'] = url
            self.stats['videos_processed'] += 1
            
            # 2. Извлечение аудио и транскрипция
            audio_data = self.extract_audio_and_subtitles(video_info)
            if not audio_data:
                return False
            
            # 3. Анализ контента с помощью ИИ
            segments = self.analyze_content_with_ai(video_info, audio_data)
            if not segments:
                self.logger.error("❌ Не удалось определить сегменты для нарезки")
                return False
            
            # 4. Создание коротких роликов
            output_files = self.create_shorts(video_info, segments)
            if not output_files:
                return False
            
            # 5. Генерация метаданных
            if self.config['features']['auto_generate_descriptions']:
                self.generate_metadata(video_info, segments, output_files)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка при обработке видео: {e}")
            self.stats['errors'] += 1
            return False
        finally:
            # Очистка временных файлов
            self.cleanup_temp_files()

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='YouTube Shorts Creator - Автоматическое создание коротких роликов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py https://www.youtube.com/watch?v=VIDEO_ID
  python main.py --config custom_config.json https://youtu.be/VIDEO_ID
  python main.py --help

Автор: SkvorikovCode (2025)
        """
    )
    
    parser.add_argument('input', help='URL YouTube видео или путь к локальному видеофайлу для обработки')
    parser.add_argument('--config', '-c', default='config.json', help='Путь к файлу конфигурации')
    parser.add_argument('--verbose', '-v', action='store_true', help='Подробный вывод')
    parser.add_argument('--version', action='version', version='YouTube Shorts Creator 1.0.0')
    
    args = parser.parse_args()
    
    try:
        # Создание экземпляра приложения
        creator = ShortsCreator(args.config)
        
        # Установка уровня логирования
        if args.verbose:
            creator.logger.setLevel(logging.DEBUG)
        
        # Вывод баннера
        creator.print_banner()
        
        # Обработка видео
        success = creator.process_video(args.input)
        
        # Вывод статистики
        creator.print_statistics()
        
        # Завершение с соответствующим кодом
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⏹️ Обработка прервана пользователем{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Fore.RED}💥 Критическая ошибка: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == '__main__':
    main()