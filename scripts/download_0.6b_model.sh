#!/bin/bash
# Download Qwen3-0.6B model for Raspberry Pi

echo "Downloading Qwen3-0.6B-Q4_K_M.gguf for Raspberry Pi..."
echo "This is a lightweight model (~400MB) optimized for faster inference on Pi 4"
echo ""

MODEL_URL="https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
MODEL_DIR="models/llm"
MODEL_FILE="$MODEL_DIR/Qwen3-0.6B-Q4_K_M.gguf"

# Create directory if it doesn't exist
mkdir -p "$MODEL_DIR"

# Check if model already exists
if [ -f "$MODEL_FILE" ]; then
    echo "Model already exists at $MODEL_FILE"
    ls -lh "$MODEL_FILE"
    echo ""
    echo "To re-download, delete the file first: rm $MODEL_FILE"
    exit 0
fi

# Download the model
echo "Downloading from: $MODEL_URL"
echo "This may take a few minutes depending on your connection..."
echo ""

if command -v wget &> /dev/null; then
    wget --show-progress -O "$MODEL_FILE" "$MODEL_URL"
elif command -v curl &> /dev/null; then
    curl -L --progress-bar -o "$MODEL_FILE" "$MODEL_URL"
else
    echo "Error: Neither wget nor curl is installed. Please install one of them."
    exit 1
fi

# Verify download
if [ -f "$MODEL_FILE" ]; then
    echo ""
    echo "✓ Download complete!"
    ls -lh "$MODEL_FILE"
    echo ""
    echo "Model is ready to use. Update your config.yaml to use:"
    echo "  model_path: \"$MODEL_FILE\""
else
    echo ""
    echo "✗ Download failed!"
    exit 1
fi
