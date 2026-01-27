---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - docs/index.md
  - docs/project-overview.md
  - docs/architecture.md
  - docs/development-guide.md
  - docs/source-tree-analysis.md
date: 2026-01-21
author: Ngoroth
---

# Product Brief: offline_translator

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

Offline Translator (Neuromancer Pi) is a high-performance, privacy-first speech-to-speech translation system designed for real-time bilingual communication in environments without internet access. The system features an innovative async pipeline architecture that enables concurrent processing of audio, text, and speech for near-zero latency. By processing speech segments while the user is still speaking (auto-segmentation), system delivers translations almost instantly after the button is released.

Unlike traditional translation apps that force users to wait through sequential processing after speaking, this solution leverages stream-based async pipelines to minimize delay. The system is designed with a Hardware Abstraction Layer (HAL) to support multiple platforms, including Windows desktops (keyboard PTT) and Raspberry Pi (GPIO PTT), making it ideal for outdoor activities like hiking and camping where internet connectivity is unavailable.

---

## Core Vision

### Problem Statement

Users need reliable real-time translation for multilingual communication (Russian, English, Ukrainian, Farsi) in offline environments such as hiking trips, remote locations, and privacy-sensitive contexts. Existing offline translation solutions suffer from unacceptable latency because they process audio sequentially: record → transcribe → translate → synthesize. This sequential approach creates frustrating delays that interrupt natural conversation flow.

### Problem Impact

Without offline real-time translation, people in internet-free environments face:
- Inability to communicate effectively with friends speaking different languages
- Forced reliance on hand gestures, drawing, or broken language
- Disconnected social experiences during outdoor activities
- Complete dependency on internet connectivity for basic communication

### Why Existing Solutions Fall Short

Current translation solutions fail to address core need because:
- **Online translators** (Google Translate, DeepL) require constant internet connection - impossible during hiking/camping
- **Offline translation devices** (Timekettle, iFlytek) suffer from sequential processing delays that interrupt conversation flow
- **Mobile apps** lack true stream processing, forcing users to wait after speaking before translation begins
- **Existing offline solutions** don't leverage modern LLM technology for nuanced, natural translation that preserves linguistic flourishes and tone

### Proposed Solution

An offline speech-to-speech translator with async concurrent pipeline architecture that processes speech, transcription, translation, and synthesis simultaneously while the user speaks. The system uses Large Language Models (LLMs) for high-quality translation that preserves linguistic nuances, idioms, and conversation tone. Configurable models allow deployment across different device capabilities (Windows desktop with GPU acceleration, Raspberry Pi with CPU-only processing). Physical PTT controls (keyboard on Windows, GPIO buttons on Raspberry Pi) provide intuitive dual-speaker interface for seamless bilingual dialogue.

### Key Differentiators

1. **Near-Zero Latency via Async Pipeline** - Concurrent processing of STT, LLM, and TTS stages with auto-segmentation during speech means translations are ready almost instantly after button release, unlike traditional sequential approaches
2. **LLM-Powered Translation** - Utilizes quantized large language models (Qwen/Llama via llama-cpp-python) for superior translation quality that captures linguistic flourishes, idioms, and conversation nuance - a significant leap over traditional translation models
3. **Complete Offline Privacy** - No data ever leaves the device, making it suitable for any context without privacy concerns or internet dependency
4. **Cross-Platform Flexibility** - Hardware Abstraction Layer (HAL) enables deployment across Windows, Raspberry Pi, and future platforms with configurable models matched to device capabilities
5. **Multi-Language Support** - Designed for Russian, English, Ukrainian, and Farsi with architecture ready for expansion to additional language pairs

---

## Target Users

### Primary Users

**Андрей, 32 года, Москва**
- Профессия: Разработчик ПО
- Языки: Русский (родной), английский (средний)
- Интересы: Хайкинг, технологии, научная фантастика
- Проблема: Хочет общаться с англоязычными друзьями, но не чувствует себя уверенно в разговорах на английском
- Текущие решения: Жесты, базовый английский, помощь друзей
- Цель: Естественное общение в походах без языковых барьеров
- Что бы сделало его счастливым: "Моментальное понимание всего, что говорится, без пауз"

**Джон, 29 лет, Сиэттл, США**
- Профессия: Project Manager
- Языки: Английский (родной)
- Интересы: Приключения, путешествия, фотография
- Проблема: Путешествует с друзьями из России/Украины/Ирана, не знает других языков
- Текущие решения: Переводчики на телефоне (не работают в походах), надежда на понимание по контексту
- Цель: Участвовать в беседах, не теряя нить из-за языковых преград
- Что бы сделало его счастливым: "Понимать шутки и культурные отсылки друзей"

**Оксана, 27 лет, Киев, Украина**
- Профессия: Маркетолог
- Языки: Украинский (родной), русский (свободный), английский (начальный)
- Интересы: Экологический туризм, волонтерство
- Проблема: В международных компаниях ей нужно переключаться между украинским/русским и английским
- Текущие решения: Переключение на русский для общения, потеря культурной идентичности
- Цель: Сохранять свою культурную идентичность в общении
- Что бы сделало её счастливой: "Могу говорить на украинском и понимают без вопросов"

**Алиреза, 34 года, Тегеран, Иран**
- Профессия: Врач
- Языки: Фарси (родной), английский (хороший)
- Интересы: Альпинизм, история, медицина
- Проблема: В международной группе ему нужен перевод для сложных тем
- Текущие решения: Английский с акцентом, потеря нюансов фарси
- Цель: Обсуждать профессиональные темы в походной обстановке
- Что бы сделало его счастливым: "Точные переводы медицинских терминов и культурных выражений"

### Secondary Users

**Не применимо** - продукт ориентирован на конечных пользователей (участников двуязычного общения)

### User Journey

**Обнаружение:**
- Андрей слышит от друга-технолога об экспериментальном офлайн переводчике
- Или находит проект на GitHub/Hacker News как FOSS решение

**Первый опыт (Onboarding):**
- Клонировать репозиторий: `git clone <repository-url>`
- Установить зависимости: `uv sync --extra dev`
- Скачать модели: `uv run python scripts/download_models.py`
- Подключить микрофон и динамики
- Настроить языки в `config.yaml`: русский↔английский, украинский↔английский, фарси↔английский
- Тест с кнопками Space/Alt (Windows) или GPIO (Raspberry Pi)

**Основное использование:**
- Приготовление к походу: зарядка портативной станции, настройка Raspberry Pi
- В походе: размещение устройства в центре лагеря
- Джон говорит по-английский (нажимает Space), говорит "The weather looks great tomorrow"
- Через 1-2 секунды после отпускания кнопки слышит на русском: "Погода завтра будет отличной"
- Андрей отвечает по-русский (нажимает Alt), говорит "Да, давайте поднимемся к вершине"
- Джон слышит на английский: "Yes, let's go to the peak"
- Диалог продолжается естественным образом без паус на "подождите, я не понял"

**Момент успеха ("Aha!"):**
- Когда в первый раз происходит непрерывный диалог без паус - никто не говорит "подождите", поток естественный
- Джон замечает: "Я не понял, что вы говорили по-русский, но перевод был мгновенным!"
- Алиреза: "Это переводчик понял персидскую идиому о 'горе за облаками'!"

**Долгосрочное использование:**
- Устройство становится обязательным для всех многонациональных походов
- Алиреза использует в экспедициях с медиками из других стран
- Группа добавляет поддержку новых языков по мере появления новых друзей
- Андрей настраивает разные профили для разных устройств (Windows дома, Raspberry Pi в походе)

---

## Success Metrics

### User Success Metrics

**Этап 1: Windows Рабочая Версия**
- **Задержка перевода:** Перевод готов в течение ≤1 секунды после отпускания кнопки PTT
- **Качество перевода:** Диалог длительностью 2 минуты на бытовые темы переведен качественно и понятно для обоих участников
- **Тестирование:** Проверка автором на 2 разных языках + тестирование с женой
- **Критерий успеха:** Естественный поток диалога без повторений "я не понял"

**Этап 2: Raspberry Pi Автономность**
- **Задержка перевода:** Перевод готов в течение ≤1 секунды на Raspberry Pi (та же производительность, что на Windows)
- **Автономность:** Устройство работает независимо без подключения к ноутбуку/ПК
- **Критерий успеха:** Полностью автономный переводчик на базе Raspberry Pi готов к использованию в полевых условиях (походы, без электричества)

**Этап 3: Публикация в Открытый Доступ**
- **Критерий успеха:** Код опубликован в открытом доступе (например, на GitHub)
- **Сам факт публикации:** Достаточным показателем успеха является доступность проекта для сообщества

### Business Objectives

**Не применимо** - проект является FOSS с открытым исходным кодом без коммерческих целей. Основной целью является создание функционального решения для личного использования и последующая публикация для сообщества.

### Key Performance Indicators

**Этап 1: Windows**
- KPI 1.1: Время отклика перевода ≤1 секунды после отпускания кнопки (измерение: хронометраж 10 тестовых фраз)
- KPI 1.2: Качество перевода диалога 2 минуты на бытовые темы = "хорошо/отлично" по субъективной оценке
- KPI 1.3: Успешное прохождение тестирования автором (2 языка) + женой

**Этап 2: Raspberry Pi**
- KPI 2.1: Время отклика перевода ≤1 секунды на Raspberry Pi (измерение: те же 10 тестовых фраз)
- KPI 2.2: Устройство функционирует автономно без внешнего компьютера (проверка: устройство включается, обрабатывает аудио, воспроизводит перевод автономно)

**Этап 3: Публикация**
- KPI 3.1: Код доступен в публичном репозитории (например, GitHub)
- KPI 3.2: Репозиторий включает README с инструкциями по установке и использованию

---

## MVP Scope

### Core Features

**Этап 1: Windows MVP (русскоязычный↔английская пара)**

- **Windows платформа с PTT управлением**
  - Space кнопка: English → Russian
  - Alt кнопка: Russian → English
  - Hold для записи, release для воспроизведения перевода

- **Async pipeline architecture**
  - STT (faster-whisper): распознавание речи в реальном времени
  - LLM (llama-cpp-python): перевод с сохранением нюансов
  - TTS (piper-tts): синтез речи
  - Все три сервиса работают concurrently для минимальной задержки

- **Ключевые функции**
  - Авто-сегментация речи во время разговора (пока нажата кнопка)
  - Barge-in: прерывание воспроизведения при нажатии любой PTT кнопки
  - Одна языковая пара: русский↔английский

- **Hardware Abstraction Layer (HAL)**
  - Аудио ввод/вывод через PortAudio (sounddevice)
  - PTT ввод через pynput (Windows keyboard)
  - Архитектура готова для расширения (Raspberry Pi GPIO на Этап 2)

- **Конфигурационная система**
  - Config YAML для настройки:
    - Пути к моделям STT, LLM, TTS
    - Языковые пары для каждого спикера
    - Частота дискретизации аудио (16kHz mono float32)
    - Настройки VAD (Voice Activity Detection)

- **Покрытие тестами**
  - Юнит-тесты для каждого компонента (audio, input, output, services: stt, translator, tts)
  - Интеграционные тесты для всего async pipeline
  - 12 тестов уже реализованы в проекте

### Out of Scope for MVP

**Отложено на Этап 2 (Raspberry Pi):**
- Raspberry Pi версия и GPIO кнопки
- Автономное устройство без компьютера

**Отложено на будущее (v2.0+):**
- Поддержка украинского и фарси языков
- Дополнительные языковые пары кроме русский↔английский
- Веб-интерфейс или GUI (CLI только для MVP)
- Облачный режим (только офлайн)
- Поддержка других устройств (только Windows для MVP)
- Менеджер моделей с авто-загрузкой (скачивание через скрипт `download_models.py` достаточно)
- Расширенные настройки аудио (настройки по умолчанию)
- Продвинутое логирование и мониторинг производительности
- Recovery и обработка сложных ошибок (базовая обработка достаточна)

### MVP Success Criteria

**Этап 1: Windows MVP**

- **KPI 1.1:** Время отклика перевода ≤1 секунды после отпускания кнопки (хронометраж 10 тестовых фраз)
- **KPI 1.2:** Качество перевода диалога 2 минуты на бытовые темы = "хорошо/отлично" по субъективной оценке
- **KPI 1.3:** Успешное прохождение тестирования автором (английский и русский) + женой
- **KPI 1.4:** Все 12 тестов (unit + integration) проходят успешно (`pytest`)

**Go/No-Go решение для перехода на Этап 2:**
- Все KPI для Этапа 1 достигнуты
- Архитектура проекта стабильна и понятна
- Конфигурационная система работает как ожидается

### Future Vision

**Этап 2: Raspberry Pi автономность**
- GPIO кнопки для PTT вместо клавиатуры
- Автономное устройство (не требует подключения к ноутбуку)
- Та же задержка ≤1 секунды на Raspberry Pi CPU
- Портативная энергия (power bank)

**Этап 3: Публикация в открытый доступ**
- FOSS проект на GitHub
- README с инструкциями по установке и использованию
- Сообщество может настраивать свои языковые пары через конфигурацию

**Дальнейшее развитие (v2.0+):**
- Поддержка украинского и фарси языков
- Множественные языковые пары (R↔E, U↔E, F↔E и т.д.)
- Мобильная версия (Android/iOS)
- Web интерфейс для конфигурации
- Контекстная память диалога для более точного перевода
- Дообучение LLM для специфических доменов (медицина, туризм)
- Облачный fallback опционально для больших моделей
