import subprocess
import os


def test_arecord():
    output_file = "test_arecord_native.wav"
    duration = 5

    # Command: Record 5 seconds at 16000Hz, S16_LE, Mono using 'plughw:2,0'
    # NOTE: Using plughw allows ALSA to handle resampling (48k -> 16k) automatically.
    # If device is hw:2,0, we force rate conversion via software plugin.

    device = "plughw:2,0"

    print(f"Recording {duration}s from {device} using native 'arecord'...")

    cmd = [
        "arecord",
        "-D",
        device,
        "-f",
        "S16_LE",
        "-r",
        "16000",
        "-c",
        "1",
        "-d",
        str(duration),
        output_file,
    ]

    try:
        # Run command directly
        _ = subprocess.run(cmd, check=True, capture_output=True)
        print(f"Success! Saved to {output_file}")

        # Check file size
        size = os.path.getsize(output_file)
        print(f"File size: {size} bytes")

        if size < 1000:
            print("WARNING: File is too small! Recording failed?")
        else:
            print("Recording looks valid.")

    except subprocess.CalledProcessError as e:
        print(f"Error running arecord: {e}")
        stderr_val = getattr(e, "stderr", None)
        if stderr_val is not None and isinstance(stderr_val, bytes):
            stderr_str: str = stderr_val.decode()
            print(f"Stderr: {stderr_str}")
    except FileNotFoundError:
        print("Error: 'arecord' not found. Is alsa-utils installed?")


if __name__ == "__main__":
    test_arecord()
