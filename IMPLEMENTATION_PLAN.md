# План Реализации Offline Translator

## 1. Обзор Архитектуры
Система представляет собой модульный конвейер (Pipeline), где каждый этап (STT, Перевод, TTS) является заменяемым сервисом. Конфигурация управляется через `config.yaml`.

**Поток данных:**
`Audio Input` -> `STT Engine` -> `Translation Engine` -> `TTS Engine` -> `Audio Output`

**Технологический стек:**
- **Язык:** Python 3.14
- **STT:** `faster-whisper` (CTranslate2)
- **LLM:** `llama.cpp-python` (GGUF)
- **TTS:** `piper-tts` (ONNX)
- **Audio:** `sounddevice`
- **Config:** `PyYAML`

---

## 2. Этапы Реализации

### Фаза 1: Фундамент и Инфраструктура
**Цель:** Подготовить проект, настройку и работу с аудио/устройствами.

1.  **Структура проекта:**
    - Создать директории: `src/app/core`, `src/app/services`, `models/stt`, `models/llm`, `models/tts`.
2.  **Конфигурация (`src/app/settings.py`):**
    - Реализовать загрузчик `config.yaml` (используя Pydantic).
    - **Важно:** Обновить текущий `config.yaml` под новую структуру (удалить старые профили "Neuromancer", сделать единую структуру).
3.  **HAL (Hardware Abstraction Layer):**
    - `InputInterface`: Абстракция для PTT (Push-to-Talk).
    - `WindowsInput`: Реализация через клавиатуру (Spacebar) с использованием `pynput`.
    - `OutputInterface`: Абстракция для вывода статусов (Console/LED).
4.  **Аудио Сервис (`src/app/core/audio.py`):**
    - Запись звука через `sounddevice` (blocking или callback).
    - Воспроизведение потока.

### Фаза 2: Сервисы ИИ (Core Logic)
**Цель:** Реализовать обертки вокруг ML моделей.

5.  **Менеджер Моделей (`downloader.py`):**
    - Скрипт для автоматического скачивания весов моделей (Whisper int8, Qwen GGUF, Piper ONNX), чтобы не хранить их в git.
6.  **STT Сервис (`src/app/services/stt.py`):**
    - Инициализация `faster-whisper`.
    - Метод `transcribe(audio_data) -> text`.
7.  **LLM Сервис (`src/app/services/translator.py`):**
    - Инициализация `Llama` (из `llama_cpp`).
    - Промптинг для перевода (System prompt + User text).
8.  **TTS Сервис (`src/app/services/tts.py`):**
    - Инициализация `piper`.
    - Метод `synthesize(text) -> audio_stream`.

### Фаза 3: Оркестрация и CLI
**Цель:** Соединить всё вместе.

9.  **Главный цикл (`src/app/main.py`):**
    - State Machine: `IDLE` -> `RECORDING` (пока нажата кнопка) -> `PROCESSING` -> `PLAYING`.
    - Логирование этапов в консоль.
10. **Интеграционный тест:**
    - Проверка полного цикла на Windows: Голос -> Текст (Ru) -> Перевод (En) -> Голос (En).

### Фаза 4: Портирование на Raspberry Pi (Будущее)
*Этот этап за рамками текущей итерации, но код пишется с учетом этого.*
- Замена `WindowsInput` на `RPiInput` (GPIO).
- Оптимизация параметров моделей (RAM usage).

---

## 3. Задачи (Todo List)

- [ ] Настроить `config.yaml` (переписать текущий).
- [ ] Реализовать `Settings` loader.
- [ ] Реализовать `AudioRecorder` и `AudioPlayer`.
- [ ] Реализовать `KeyboardListener` для Windows.
- [ ] Скачать тестовые модели (tiny/small).
- [ ] Реализовать `STTService`.
- [ ] Реализовать `LLMService`.
- [ ] Реализовать `TTSService`.
- [ ] Написать `main.py` loop.
