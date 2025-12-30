"""
Cross-Platform GameMode Detection
Detects when the user is gaming and should pause AI processing.
"""
import platform
import logging

logger = logging.getLogger("worker.gamemode")

# Platform-specific process names
GAMEMODE_PROCESSES = {
    "Windows": [
        "steam.exe", "steamwebhelper.exe",
        "cs2.exe", "csgo.exe",
        "dota2.exe", 
        "valorant.exe", "valorant-win64-shipping.exe",
        "r5apex.exe",  # Apex Legends
        "cod.exe", "modernwarfare.exe",
        "gta5.exe", "gtavlauncher.exe",
        "cyberpunk2077.exe",
        "eldenring.exe",
        "baldursgate3.exe", "bg3.exe",
        "starfield.exe",
    ],
    "Linux": [
        "steam", "steamwebhelper",
        "cs2_linux64", "csgo_linux64",
        "dota2",
        "wine", "wine64",  # For Windows games via Proton/Wine
        "gamescope",  # Steam Deck
        "lutris",
    ],
    "Darwin": [  # macOS
        "Steam", "steam_osx",
        "World of Warcraft",
        "Baldur's Gate 3",
        "Civilization",
        "Cities Skylines",
    ],
}


def get_running_processes() -> set:
    """Get set of running process names, platform-independent."""
    system = platform.system()
    
    try:
        import psutil
        processes = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info.get('name')
                if name:
                    processes.add(name.lower() if system == "Windows" else name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes
    except ImportError:
        logger.warning("psutil not installed, GameMode detection disabled")
        return set()


def check_gamemode() -> tuple[bool, str | None]:
    """
    Check if any gaming processes are running.
    
    Returns:
        Tuple of (is_gaming: bool, game_name: str | None)
    """
    system = platform.system()
    game_processes = GAMEMODE_PROCESSES.get(system, [])
    
    if not game_processes:
        logger.debug(f"No game processes defined for {system}")
        return False, None
    
    running = get_running_processes()
    
    # Normalize for comparison
    if system == "Windows":
        game_processes_lower = [p.lower() for p in game_processes]
        for proc in running:
            if proc in game_processes_lower:
                # Find original name for display
                idx = game_processes_lower.index(proc)
                return True, game_processes[idx]
    else:
        for game in game_processes:
            if game in running:
                return True, game
    
    return False, None


def add_game_process(process_name: str, system: str = None):
    """Add a custom game process to the detection list."""
    if system is None:
        system = platform.system()
    
    if system in GAMEMODE_PROCESSES:
        if process_name not in GAMEMODE_PROCESSES[system]:
            GAMEMODE_PROCESSES[system].append(process_name)
            logger.info(f"Added '{process_name}' to GameMode detection for {system}")


if __name__ == "__main__":
    # Test GameMode detection
    logging.basicConfig(level=logging.DEBUG)
    
    print(f"Platform: {platform.system()}")
    print(f"Monitored processes: {GAMEMODE_PROCESSES.get(platform.system(), [])}")
    
    is_gaming, game = check_gamemode()
    if is_gaming:
        print(f"🎮 GameMode ACTIVE: {game}")
    else:
        print("✅ GameMode inactive - no games detected")
