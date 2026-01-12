"""
Cross-Platform Insomnia Protocol
Prevents system sleep during worker operation on Windows, Linux, and macOS.
"""
import platform
import subprocess
import logging
from contextlib import contextmanager

logger = logging.getLogger("worker.insomnia")

class InsomniaContext:
    """
    Context manager that prevents the system from sleeping.
    Works on Windows, Linux, and macOS.
    """
    
    def __init__(self):
        self.system = platform.system()
        self.process = None
        self._windows_previous_state = None
    
    def __enter__(self):
        logger.info(f"Enabling Insomnia Protocol on {self.system}")
        
        if self.system == "Windows":
            self._enable_windows()
        elif self.system == "Darwin":  # macOS
            self._enable_macos()
        elif self.system == "Linux":
            self._enable_linux()
        else:
            logger.warning(f"Unsupported platform: {self.system}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Disabling Insomnia Protocol")
        
        if self.system == "Windows":
            self._disable_windows()
        elif self.process:
            self.process.terminate()
            self.process = None
        
        return False
    
    def _enable_windows(self):
        """Windows: Use SetThreadExecutionState API"""
        try:
            import ctypes
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            
            self._windows_previous_state = ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            logger.debug("Windows: SetThreadExecutionState activated")
        except Exception as e:
            logger.warning(f"Windows Insomnia failed: {e}")
    
    def _disable_windows(self):
        """Windows: Reset execution state"""
        try:
            import ctypes
            ES_CONTINUOUS = 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            logger.debug("Windows: SetThreadExecutionState reset")
        except Exception as e:
            logger.warning(f"Windows Insomnia reset failed: {e}")
    
    def _enable_macos(self):
        """macOS: Use caffeinate command"""
        try:
            # -i: Prevent idle sleep
            # -d: Prevent display sleep
            self.process = subprocess.Popen(
                ["caffeinate", "-id"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug("macOS: caffeinate started")
        except FileNotFoundError:
            logger.warning("macOS: caffeinate not found")
        except Exception as e:
            logger.warning(f"macOS Insomnia failed: {e}")
    
    def _enable_linux(self):
        """Linux: Use systemd-inhibit or gnome-session-inhibit"""
        # Try systemd-inhibit first (works on most modern Linux)
        try:
            self.process = subprocess.Popen(
                ["systemd-inhibit", "--what=idle:sleep", "--who=Conductor", 
                 "--why=AI Processing", "sleep", "infinity"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug("Linux: systemd-inhibit started")
            return
        except FileNotFoundError:
            pass
        
        # Fallback: gnome-session-inhibit
        try:
            self.process = subprocess.Popen(
                ["gnome-session-inhibit", "--inhibit=idle", "--reason=AI Processing",
                 "sleep", "infinity"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug("Linux: gnome-session-inhibit started")
            return
        except FileNotFoundError:
            pass
        
        # Fallback: xdg-screensaver
        try:
            self.process = subprocess.Popen(
                ["xdg-screensaver", "suspend", "$$"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug("Linux: xdg-screensaver started")
        except FileNotFoundError:
            logger.warning("Linux: No sleep inhibitor found (systemd-inhibit, gnome-session-inhibit, xdg-screensaver)")


@contextmanager
def prevent_sleep():
    """Convenience context manager for preventing sleep."""
    ctx = InsomniaContext()
    try:
        ctx.__enter__()
        yield ctx
    finally:
        ctx.__exit__(None, None, None)


if __name__ == "__main__":
    # Test the insomnia protocol
    import time
    logging.basicConfig(level=logging.DEBUG)
    
    print(f"Testing Insomnia on {platform.system()}...")
    with InsomniaContext():
        print("Sleep prevention active. Press Ctrl+C to stop.")
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            pass
    print("Insomnia disabled.")
