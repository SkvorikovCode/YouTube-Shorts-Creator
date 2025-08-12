# YouTube Shorts Creator 🎬

> Автоматическое создание коротких роликов из YouTube видео с использованием искусственного интеллекта

**Автор:** SkvorikovCode  
**Год:** 2025  
**Версия:** 1.0.0

## 📋 Описание

YouTube Shorts Creator — это Python-скрипт, который автоматически создает короткие ролики (shorts) из длинных YouTube видео. Программа использует современные технологии ИИ для анализа контента и определения наиболее интересных моментов для нарезки.

### ✨ Основные возможности

- 📥 **Скачивание видео** с YouTube в высоком качестве
- 🤖 **ИИ-анализ контента** через Ollama (llama3.2, mistral, codellama)
- 🎵 **Транскрипция аудио** с помощью OpenAI Whisper
- ✂️ **Интеллектуальная нарезка** на основе анализа контента
- 📝 **Автоматическая генерация** названий и описаний
- 🎨 **Цветной консольный интерфейс** с прогресс-барами
- 📊 **Подробное логирование** всех операций
- 🔧 **Гибкая настройка** через конфигурационный файл

## 🚀 Быстрый старт

### Предварительные требования

1. **Python 3.9+**
2. **FFmpeg** (для обработки видео)
3. **Ollama** (для ИИ-анализа)

### Установка зависимостей

#### macOS

```bash
# Установка FFmpeg через Homebrew
brew install ffmpeg

# Установка Ollama
brew install ollama

# Запуск Ollama и загрузка модели
ollama serve
ollama pull llama3.2
```

#### Windows

```powershell
# Установка FFmpeg через Chocolatey
choco install ffmpeg

# Скачайте Ollama с официального сайта: https://ollama.ai
# После установки:
ollama serve
ollama pull llama3.2
```

#### Linux (Ubuntu/Debian)

```bash
# Установка FFmpeg
sudo apt update
sudo apt install ffmpeg

# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.2
```

### Установка Python зависимостей

```bash
# Клонирование репозитория
git clone https://github.com/SkvorikovCode/Shorts-Creator.git
cd Shorts-Creator

# Создание виртуального окружения (рекомендуется)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

## 📖 Использование

### Базовое использование

```bash
# Создание shorts из YouTube видео
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Расширенные опции

```bash
# С подробным выводом
python main.py -v "https://youtu.be/VIDEO_ID"

# С кастомной конфигурацией
python main.py -c custom_config.json "https://www.youtube.com/watch?v=VIDEO_ID"

# Справка по командам
python main.py --help
```

### Примеры команд

```bash
# Обработка популярного видео
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Обработка с максимальным логированием
python main.py --verbose "https://youtu.be/jNQXAC9IVRw"
```

## ⚙️ Конфигурация

Основные настройки находятся в файле `config.json`:

```json
{
  "video": {
    "max_short_duration": 60,
    "min_short_duration": 15,
    "video_quality": "720p"
  },
  "ai": {
    "ollama": {
      "model": "llama3.2",
      "base_url": "http://localhost:11434"
    },
    "whisper": {
      "model": "base"
    }
  }
}
```

### Настройка моделей ИИ

#### Ollama модели

```bash
# Доступные модели для анализа
ollama pull llama3.2      # Рекомендуется (быстрая и точная)
ollama pull mistral       # Альтернатива
ollama pull codellama     # Для технического контента
```

#### Whisper модели

- `tiny` - самая быстрая, низкое качество
- `base` - баланс скорости и качества (по умолчанию)
- `small` - лучшее качество, медленнее
- `medium` - высокое качество
- `large` - максимальное качество, очень медленная

## 📁 Структура выходных файлов

```
output/
└── Название_видео/
    ├── short_001.mp4
    ├── short_002.mp4
    ├── short_003.mp4
    └── metadata/
        ├── short_001_metadata.json
        ├── short_002_metadata.json
        └── short_003_metadata.json
```

### Пример метаданных

```json
{
  "original_video": {
    "title": "Название исходного видео",
    "duration": 1200
  },
  "short": {
    "file_path": "./output/video/short_001.mp4",
    "start_time": 120,
    "end_time": 180,
    "title": "Интересный момент из видео",
    "description": "Краткое описание содержания",
    "relevance_score": 0.85
  }
}
```

## 🔧 Расширенная настройка

### Настройка качества видео

```json
{
  "video": {
    "video_quality": "1080p",  // 480p, 720p, 1080p
    "audio_quality": "192k",   // 128k, 192k, 320k
    "output_format": "mp4"     // mp4, avi, mov
  }
}
```

### Настройка производительности

```json
{
  "processing": {
    "max_concurrent_jobs": 2,
    "ffmpeg_threads": 4,
    "enable_gpu_acceleration": false
  }
}
```

### Настройка ИИ-анализа

```json
{
  "ai": {
    "ollama": {
      "model": "llama3.2",
      "timeout": 300,
      "max_tokens": 2048
    }
  }
}
```

## 🐛 Устранение неполадок

### Частые проблемы

#### 1. Ошибка "FFmpeg not found"

```bash
# Проверьте установку FFmpeg
ffmpeg -version

# Если не установлен, установите:
# macOS: brew install ffmpeg
# Windows: choco install ffmpeg
# Linux: sudo apt install ffmpeg
```

#### 2. Ошибка подключения к Ollama

```bash
# Убедитесь, что Ollama запущен
ollama serve

# Проверьте доступность API
curl http://localhost:11434/api/version
```

#### 3. Ошибки при скачивании видео

```bash
# Обновите yt-dlp до последней версии
pip install --upgrade yt-dlp

# Проверьте доступность видео
yt-dlp --list-formats "URL_ВИДЕО"
```

#### 4. Проблемы с памятью

- Используйте модель Whisper `tiny` или `base`
- Уменьшите `max_concurrent_jobs` в конфигурации
- Включите `preserve_temp_files: false`

### Логи и отладка

```bash
# Запуск с подробным логированием
python main.py --verbose "URL_ВИДЕО"

# Логи сохраняются в папке logs/
ls logs/
```

## 📊 Производительность

### Рекомендуемые системные требования

- **CPU:** 4+ ядра
- **RAM:** 8+ GB
- **Диск:** 10+ GB свободного места
- **Интернет:** Стабильное соединение для скачивания

### Время обработки (примерно)

| Длительность видео | Время обработки | Модель Whisper |
|-------------------|-----------------|----------------|
| 10 минут          | 2-3 минуты      | base           |
| 30 минут          | 5-8 минут       | base           |
| 60 минут          | 10-15 минут     | base           |

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 🙏 Благодарности

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - для скачивания видео
- [OpenAI Whisper](https://github.com/openai/whisper) - для транскрипции
- [Ollama](https://ollama.ai) - для ИИ-анализа
- [FFmpeg](https://ffmpeg.org) - для обработки видео

## 📞 Поддержка

Если у вас есть вопросы или предложения:

- 🐛 [Создайте issue](https://github.com/SkvorikovCode/Shorts-Creator/issues)
- 💬 [Обсуждения](https://github.com/SkvorikovCode/Shorts-Creator/discussions)
- 📧 Email: [ваш-email@example.com]

---

**Сделано с ❤️ автором SkvorikovCode в 2025 году**

> 🌟 Если проект оказался полезным, поставьте звездочку на GitHub!