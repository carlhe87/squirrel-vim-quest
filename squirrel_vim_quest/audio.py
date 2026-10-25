"""Speech (Windows built-in voice) and small sound effects.

Speech uses SAPI directly with the async + purge flags, so a call returns at
once and a new line cuts off the one still being spoken. Sound effects are
tiny generated .wav files played with winsound. Everything fails quietly:
the game must still run with no audio at all. SVQ_MUTE=1 turns it all off.
"""

from __future__ import annotations

import math
import os
import struct
import wave
from pathlib import Path

try:
    import winsound
except ImportError:  # not Windows
    winsound = None

SVSF_ASYNC = 1
SVSF_PURGE_BEFORE_SPEAK = 2

# strings language -> Windows primary language id (low bits of the voice's LCID)
PRIMARY_LANGUAGE = {"en": 0x09, "de": 0x07, "zh": 0x04, "sv": 0x1D}

# name -> list of (frequency Hz, seconds)
EFFECTS: dict[str, list[tuple[int, float]]] = {
    "hop": [(880, 0.03)],
    "wrong": [(260, 0.09)],
    "eat": [(660, 0.06), (990, 0.09)],
    "bump": [(200, 0.08), (150, 0.14)],
    "star": [(784, 0.08), (988, 0.08), (1175, 0.14)],
    "gate": [(392, 0.1), (523, 0.1), (659, 0.18)],
    "win": [(523, 0.11), (659, 0.11), (784, 0.11), (1047, 0.3)],
}


def _write_wav(path: Path, notes: list[tuple[int, float]], rate: int = 22050, volume: float = 0.25) -> None:
    frames = bytearray()
    for freq, seconds in notes:
        n = int(rate * seconds)
        for i in range(n):
            fade = min(1.0, i / (rate * 0.004), (n - i) / (rate * 0.015))
            sample = volume * fade * math.sin(2 * math.pi * freq * i / rate)
            frames += struct.pack("<h", int(sample * 32767))
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(bytes(frames))


class Audio:
    def __init__(self, sfx_dir: Path, sound_on: bool = True, lang: str = "en") -> None:
        self.muted_by_env = bool(os.environ.get("SVQ_MUTE"))
        self.sound_on = sound_on
        self.last_line = ""
        self._sfx_dir = sfx_dir
        self._voice = None
        if self.muted_by_env:
            return
        try:
            import comtypes.client

            self._voice = comtypes.client.CreateObject("SAPI.SpVoice")
            self._voice.Rate = -1  # a little slower for young ears
            self._pick_voice(lang)
        except Exception:
            self._voice = None
        try:
            sfx_dir.mkdir(parents=True, exist_ok=True)
            for name, notes in EFFECTS.items():
                path = sfx_dir / f"{name}.wav"
                if not path.exists():
                    _write_wav(path, notes)
        except OSError:
            pass

    def _pick_voice(self, lang: str) -> None:
        """Use an installed voice for lang; the system default may be another language."""
        wanted = PRIMARY_LANGUAGE.get(lang)
        voices = self._voice.GetVoices()
        for i in range(voices.Count):
            voice = voices.Item(i)
            try:
                lcid = int(voice.GetAttribute("Language").split(";")[0], 16)
            except Exception:
                continue
            if lcid & 0x3FF == wanted:
                self._voice.Voice = voice
                return

    @property
    def active(self) -> bool:
        return self.sound_on and not self.muted_by_env

    def say(self, text: str) -> None:
        self.last_line = text
        if self.active and self._voice is not None:
            try:
                self._voice.Speak(text, SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
            except Exception:
                pass

    def repeat(self) -> None:
        if self.last_line:
            self.say(self.last_line)

    def play(self, name: str) -> None:
        if not self.active or winsound is None:
            return
        path = self._sfx_dir / f"{name}.wav"
        try:
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except RuntimeError:
            pass

    def set_sound(self, on: bool) -> None:
        self.sound_on = on
        if not on:
            if self._voice is not None:
                try:
                    self._voice.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
                except Exception:
                    pass
            if winsound is not None:
                winsound.PlaySound(None, 0)
