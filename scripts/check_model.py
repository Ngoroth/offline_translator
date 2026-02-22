from huggingface_hub import list_repo_files

try:
    repo_id = "Qwen/Qwen3-0.6B-GGUF"
    files = list_repo_files(repo_id)
    print(f"Files in {repo_id}:")
    for f in files:
        if f.endswith(".gguf"):
            print(f" - {f}")
except Exception as e:
    print(f"Error listing files: {e}")
