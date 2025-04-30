import torch
import time

def get_gpu_memory_usage(device_id: int = 0) -> dict:
    """
    Retrieves the current GPU memory usage for a specific device.

    Args:
        device_id: The ID of the GPU device to check. Defaults to 0.

    Returns:
        A dictionary containing memory usage details:
        {
            "device_name": str,
            "total_memory_gb": float,
            "allocated_memory_gb": float,
            "reserved_memory_gb": float,
            "free_memory_gb": float,
            "usage_percent": float
        }
        Returns an empty dictionary if CUDA is not available or the device ID is invalid.
    """
    if not torch.cuda.is_available():
        print("CUDA is not available. Cannot monitor GPU memory.")
        return {}

    if device_id >= torch.cuda.device_count():
        print(f"Error: Invalid device ID {device_id}. Available devices: {torch.cuda.device_count()}")
        return {}

    try:
        device_name = torch.cuda.get_device_name(device_id)
        total_memory = torch.cuda.get_device_properties(device_id).total_memory
        allocated_memory = torch.cuda.memory_allocated(device_id)
        reserved_memory = torch.cuda.memory_reserved(device_id) # PyTorch's cache

        total_memory_gb = total_memory / (1024**3)
        allocated_memory_gb = allocated_memory / (1024**3)
        reserved_memory_gb = reserved_memory / (1024**3)
        # Free memory calculation can be tricky; using total - reserved as an estimate
        free_memory_gb = (total_memory - reserved_memory) / (1024**3)
        usage_percent = (reserved_memory / total_memory) * 100 if total_memory > 0 else 0

        return {
            "device_name": device_name,
            "total_memory_gb": round(total_memory_gb, 2),
            "allocated_memory_gb": round(allocated_memory_gb, 2),
            "reserved_memory_gb": round(reserved_memory_gb, 2),
            "free_memory_gb": round(free_memory_gb, 2),
            "usage_percent": round(usage_percent, 1)
        }
    except Exception as e:
        print(f"Error getting GPU memory info for device {device_id}: {e}")
        return {}

def monitor_gpu_memory(interval_seconds: int = 5, device_id: int = 0):
    """
    Continuously monitors and prints GPU memory usage at specified intervals.

    Args:
        interval_seconds: The time interval (in seconds) between checks.
        device_id: The ID of the GPU device to monitor.
    """
    if not torch.cuda.is_available():
        print("CUDA not available. Exiting GPU monitor.")
        return

    print(f"Starting GPU memory monitor for device {device_id} (refresh every {interval_seconds}s)... Press Ctrl+C to stop.")
    try:
        while True:
            usage = get_gpu_memory_usage(device_id)
            if usage:
                print(f"[{time.strftime('%H:%M:%S')}] GPU {device_id} ({usage['device_name']}): "
                      f"Used: {usage['reserved_memory_gb']:.2f}/{usage['total_memory_gb']:.2f} GB "
                      f"({usage['usage_percent']:.1f}%) | "
                      f"Allocated: {usage['allocated_memory_gb']:.2f} GB")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Could not retrieve GPU info.")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\nStopping GPU memory monitor.")
    except Exception as e:
        print(f"\nError during GPU monitoring: {e}")

if __name__ == "__main__":
    print("--- GPU Memory Check ---")
    usage_info = get_gpu_memory_usage()
    if usage_info:
        print(f"Device: {usage_info['device_name']}")
        print(f"Total Memory: {usage_info['total_memory_gb']} GB")
        print(f"Allocated Memory: {usage_info['allocated_memory_gb']} GB")
        print(f"Reserved (Cached) Memory: {usage_info['reserved_memory_gb']} GB")
        print(f"Estimated Free Memory: {usage_info['free_memory_gb']} GB")
        print(f"Usage Percentage: {usage_info['usage_percent']}%")
    else:
        print("Could not retrieve GPU memory information.")

    # Example of continuous monitoring (uncomment to run)
    # print("\n--- Starting Continuous Monitoring (Press Ctrl+C to stop) ---")
    # monitor_gpu_memory(interval_seconds=5)