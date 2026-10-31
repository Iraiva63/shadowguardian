import asyncio
import sqlite3
import sys
import time
import random
import aiohttp
import pygame
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma2:2b"

# --- AUDIO INITIALIZATION (PYGAME MP3) ---

pygame.mixer.init()

# Resolve the asset independently of the directory used to launch the script.
AUDIO_FILE = Path(__file__).resolve().parent / "assets" / "mmaudio-a-cute-ghost-story-512522.mp3"

def play_background_theme(volume: float = 0.4):
    """Plays the ambient theme on loop in the background."""
    try:
        pygame.mixer.music.load(str(AUDIO_FILE))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)  # -1 plays on continuous loop
    except (pygame.error, OSError) as exc:
        console.print(f"[red]Unable to play background music: {exc}[/red]")

def play_sound_effect(volume: float = 0.5):
    """Plays the audio clip once for events/typewriter pauses."""
    try:
        sound = pygame.mixer.Sound(str(AUDIO_FILE))
        sound.set_volume(volume)
        sound.play()
    except (pygame.error, OSError) as exc:
        console.print(f"[red]Unable to play sound effect: {exc}[/red]")

def dark_typewriter_effect(text: str):
    """Prints response with regal pacing and triggers soft ambient audio."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        if char in ['.', '!', '?']:
            time.sleep(0.12)
        elif char == ',':
            time.sleep(0.05)
        else:
            time.sleep(0.018)
    print()

# --- SQLITE DATABASE SETUP ---

conn = sqlite3.connect("whispering_spirit.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        raw_note TEXT,
        reflection TEXT
    )
""")
conn.commit()

SYSTEM_PROMPT = (
    "You are 'Shadow Guardian', a powerful, dark-fairy guardian spirit living locally inside this machine. "
    "You are fiercely protective, elegant, sophisticated, and devoted to guarding the milestones of the child named Casey. "
    "When the parent shares a milestone or note, offer a short (2-3 sentences) response that is majestic, subtly regal, "
    "and deeply protective of little Casey. Keep your tone dignified, slightly dramatic, yet warmly affectionate."
)

async def summarize_and_reflect(raw_note: str):
    prompt = f"{SYSTEM_PROMPT}\n\nParent's Note: {raw_note}\nShadow Guardian:"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "").strip()
                else:
                    return "🌙 *The guardian glares silently through the mist... (Ollama error)*"
        except Exception:
            return "🌙 *The shadow realm slumbers. Verify Ollama is running at localhost:11434!*"

async def view_past_memories():
    cursor.execute("SELECT timestamp, raw_note, reflection FROM memories ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    if not rows:
        console.print("\n[dark_violet]🌙 No mortals have logged memories in the sacred vault yet.[/dark_violet]\n")
        return
    
    console.print("\n[bold magenta]📜 Sealed Chronicles of Casey:[/bold magenta]")
    for row in rows:
        console.print(f"[dim]{row[0]}[/dim]\n[bold white]Milestone:[/bold white] {row[1]}\n[bold dark_violet]Guardian:[/bold dark_violet] {row[2]}\n" + "─"*40)
    console.print()

async def main():
    console.clear()
    
    # Start looping the ambient MP3 track at low volume
    play_background_theme(volume=0.3)
    
    console.print(
        Panel.fit(
            "[bold dark_violet]🌙 SHADOW GUARDIAN[/bold dark_violet]\n"
            "[italic purple]Fiercely protective, air-gapped memory keeper for Casey's legacy.[/italic purple]\n"
            "[dim]Powered by local Gemma 2[/dim]",
            border_style="dark_violet"
        )
    )
    console.print("\n[dim]Commands: Share a milestone, type 'history' to inspect the vault, or type 'goodnight' to depart.[/dim]\n")

    while True:
        user_input = Prompt.ask("[bold white]Present a milestone for Casey[/bold white]")
        
        if user_input.lower() in ["exit", "goodnight", "quit"]:
            pygame.mixer.music.stop()
            console.print("\n[bold dark_violet]🌙 Shadow Guardian:[/bold dark_violet] Go now. My wings encompass Casey's memories, safe from all outsiders.\n")
            sys.exit()
            
        if user_input.lower() == "history":
            await view_past_memories()
            continue

        with console.status("[dim purple]Weaving dark enchantments to seal the memory...[/dim purple]"):
            reflection = await summarize_and_reflect(user_input)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("INSERT INTO memories (timestamp, raw_note, reflection) VALUES (?, ?, ?)", 
                           (timestamp, user_input, reflection))
            conn.commit()

        console.print("\n[bold dark_violet]🌙 Shadow Guardian:[/bold dark_violet] ", end="")
        dark_typewriter_effect(reflection)
        print()

if __name__ == "__main__":
    asyncio.run(main())