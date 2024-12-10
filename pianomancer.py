import sys
import time
import os
import curses
import mido
import logging
import fluidsynth
import threading
import platform
import random
import math
import urllib.request

logging.basicConfig(
    filename='pianomancer.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

NOTE_MIDI_NUMBERS = {
    'z': 48,
    's': 49,
    'x': 50,
    'd': 51,
    'c': 52,
    'v': 53,
    'g': 54,
    'b': 55,
    'h': 56,
    'n': 57,
    'j': 58,
    'm': 59,
    ',': 60,
    'l': 61,
    '.': 62,
    ';': 63,
    '/': 64,
    'q': 65,
    'w': 67,
    'e': 69,
    'r': 71,
    't': 72,
    'y': 74,
    'u': 76,
    'i': 77,
    'o': 79,
    'p': 81,
    '=': 84,
}

MIN_HEIGHT = 30
MIN_WIDTH = 80

class SuppressStderr:
    def __enter__(self):
        self.null_fds = os.open(os.devnull, os.O_RDWR)
        self.old_stderr = os.dup(2)
        os.dup2(self.null_fds, 2)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self.old_stderr, 2)
        os.close(self.null_fds)
        os.close(self.old_stderr)

def format_time(seconds):
    mm = int(seconds // 60)
    ss = int(seconds % 60)
    return f"{mm:02d}:{ss:02d}"

def handle_resize(stdscr):
    curses.resize_term(0, 0)
    stdscr.erase()
    stdscr.refresh()

def draw_progress_bar(stdscr, midi_player):
    if not midi_player or not midi_player.is_playing:
        return
    max_y, max_x = stdscr.getmaxyx()
    if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
        return
    bar_y = max_y - 2
    try:
        stdscr.move(bar_y, 0)
        stdscr.clrtoeol()
        total_time = midi_player.get_total_length()
        current_time = midi_player.get_current_logical_time()
        if total_time <= 0:
            percentage = 0
        else:
            percentage = min(max(current_time / total_time, 0), 1.0)
        elapsed_str = format_time(current_time)
        total_str = format_time(total_time)
        time_str = f"{elapsed_str}/{total_str}"
        time_str_len = len(time_str) + 2
        bar_width = max_x - time_str_len - 4
        if bar_width < 0:
            return
        filled = int(bar_width * percentage)
        bar_str = "[" + ("█" * filled) + ("░" * (bar_width - filled)) + "]"
        display_str = f"{bar_str} {time_str}"
        stdscr.move(bar_y, 2)
        stdscr.clrtoeol()
        stdscr.addstr(bar_y, 2, display_str, curses.color_pair(7))
    except:
        pass

def draw_resize_prompt(stdscr, max_y, max_x):
    stdscr.erase()
    msg = f"Terminal too small. Please resize to at least {MIN_WIDTH}x{MIN_HEIGHT}."
    try:
        stdscr.addstr(max_y//2, max(max_x//2 - len(msg)//2, 0), msg, curses.color_pair(7))
    except:
        pass
    stdscr.refresh()

def display_scrollable_list(stdscr, items, selected, start_index, title):
    max_y, max_x = stdscr.getmaxyx()
    if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
        return
    try:
        stdscr.erase()
        stdscr.move(1, max(0, (max_x - len(title)) // 2))
        stdscr.clrtoeol()
        stdscr.addstr(1, max(0, (max_x - len(title)) // 2), title, curses.color_pair(7))
        visible_height = max_y - 6
        end_index = start_index + visible_height
        displayed_items = items[start_index:end_index]
        for idx, item in enumerate(displayed_items):
            row = idx + 3
            if row >= max_y - 4:
                break
            stdscr.move(row, 2)
            stdscr.clrtoeol()
            if (start_index + idx) == selected:
                stdscr.addstr(row, 2, f"> {item}", curses.color_pair(8))
            else:
                stdscr.addstr(row, 2, f"  {item}", curses.color_pair(7))
        instructions = "Up/Down: Move | PageUp/PageDown: Scroll | Enter: Select | Q: Cancel"
        if max_y - 3 >= 0:
            stdscr.move(max_y - 3, 2)
            stdscr.clrtoeol()
            stdscr.addstr(max_y - 3, 2, instructions, curses.color_pair(7))
        stdscr.refresh()
    except:
        pass

class ChristmasTreeDisplay:
    def __init__(self, tree_lines, color_pairs, stdscr):
        self.tree_lines = tree_lines
        self.color_pairs = color_pairs
        self.stdscr = stdscr
        self.light_states = {}
        self.min_delay = 0.5
        self.max_delay = 2.0
        self.initialize_lights()
        self.active_notes = set()
        self.note_display_start_line = len(tree_lines) + 2

    def initialize_lights(self):
        current_time = time.time()
        for line_idx, line in enumerate(self.tree_lines):
            for char_idx, char in enumerate(line):
                if char == 'O':
                    color = random.choice(self.color_pairs)
                    next_change = current_time + random.uniform(self.min_delay, self.max_delay)
                    self.light_states[(line_idx, char_idx)] = {'color': color, 'next_change': next_change}

    def update_lights(self):
        current_time = time.time()
        for position, state in self.light_states.items():
            if current_time >= state['next_change']:
                available_colors = [cp for cp in self.color_pairs if cp != state['color']]
                if not available_colors:
                    available_colors = self.color_pairs
                new_color = random.choice(available_colors)
                self.light_states[position]['color'] = new_color
                self.light_states[position]['next_change'] = current_time + random.uniform(self.min_delay, self.max_delay)

    def draw_tree(self):
        max_y, max_x = self.stdscr.getmaxyx()
        if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
            return
        try:
            for x in range(max_x):
                if 0 <= x < max_x:
                    if 0 < max_y:
                        self.stdscr.move(0, x)
                        self.stdscr.addch('-', curses.color_pair(4))
                    if max_y - 4 < max_y and max_y - 4 >= 0:
                        self.stdscr.move(max_y - 4, x)
                        self.stdscr.addch('-', curses.color_pair(4))
            for y in range(max_y):
                if 0 <= y < max_y:
                    self.stdscr.move(y, 0)
                    self.stdscr.addch('|', curses.color_pair(4))
                    self.stdscr.move(y, max_x - 1)
                    self.stdscr.addch('|', curses.color_pair(4))
            if max_y > 0 and max_x > 0:
                self.stdscr.move(0, 0)
                self.stdscr.addch('+', curses.color_pair(4))
            if max_y > 0 and max_x - 1 >= 0:
                self.stdscr.move(0, max_x - 1)
                self.stdscr.addch('+', curses.color_pair(4))
            if max_y - 4 >= 0:
                self.stdscr.move(max_y - 4, 0)
                self.stdscr.addch('+', curses.color_pair(4))
            if max_y - 4 >= 0 and max_x - 1 >= 0:
                self.stdscr.move(max_y - 4, max_x - 1)
                self.stdscr.addch('+', curses.color_pair(4))
        except:
            pass
        tree_width = max(len(line) for line in self.tree_lines)
        start_x = (max_x - tree_width) // 2
        for line_idx, line in enumerate(self.tree_lines):
            if line_idx + 1 >= max_y - 5:
                break
            for char_idx, char in enumerate(line):
                x_position = start_x + char_idx
                y_position = line_idx + 1
                if 0 <= x_position < max_x - 1 and 0 <= y_position < max_y - 4:
                    try:
                        if char == '★':
                            self.stdscr.move(y_position, x_position)
                            self.stdscr.addstr(char, curses.color_pair(7) | curses.A_BOLD)
                        elif char == 'O':
                            if (line_idx, char_idx) in self.light_states:
                                color = self.light_states[(line_idx, char_idx)]['color']
                            else:
                                color = curses.color_pair(7)
                            self.stdscr.move(y_position, x_position)
                            self.stdscr.addstr(char, color)
                        elif char == '*':
                            self.stdscr.move(y_position, x_position)
                            self.stdscr.addstr(char, curses.color_pair(2))
                        else:
                            self.stdscr.move(y_position, x_position)
                            self.stdscr.addstr(char, curses.color_pair(7))
                    except:
                        pass
        self.stdscr.noutrefresh()

    def draw_active_notes(self):
        max_y, max_x = self.stdscr.getmaxyx()
        if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
            return
        try:
            self.stdscr.move(self.note_display_start_line, 1)
            self.stdscr.clrtoeol()
            for x in range(1, max_x - 1):
                self.stdscr.move(self.note_display_start_line, x)
                self.stdscr.addch(' ', curses.color_pair(7))
        except:
            pass
        note_range = list(range(21, 109))
        max_display_x = max_x - 2
        num_notes = len(note_range)
        if num_notes == 0:
            return
        note_width = max_display_x // num_notes
        for idx, note in enumerate(note_range):
            column = 1 + idx * note_width + note_width // 2
            if note in self.active_notes:
                try:
                    self.stdscr.move(self.note_display_start_line, column)
                    self.stdscr.addstr('█', curses.color_pair(random.choice([1, 2, 3, 5, 6])))
                except:
                    pass
        self.stdscr.noutrefresh()

    def update_display(self):
        self.update_lights()
        self.draw_tree()
        self.draw_active_notes()

class MIDIPlayer:
    def __init__(self, midi_file, octave_shift, playback_speed, fs, global_active_notes, stdscr, loop_mode=False):
        try:
            self.midi = mido.MidiFile(midi_file)
            self.octave_shift = octave_shift
            self.playback_speed = playback_speed
            self.fs = fs
            self.is_playing = True
            self.interrupted = False
            self.active_notes = set()
            self.global_active_notes = global_active_notes
            self.loop_mode = loop_mode
            self.stdscr = stdscr
            self.paused = False
            self.paused_for_soundfont = False
            self.pause_start = 0.0
            self.pause_offset = 0.0
            self.paused_logical_time = 0.0
            self.prepare_messages()
            logging.info(f"MIDIPlayer initialized for file: {midi_file}")
        except:
            logging.exception("Error initializing MIDIPlayer.")
            self.is_playing = False

    def prepare_messages(self):
        try:
            self.message_queue = []
            absolute_time = 0
            for msg in self.midi:
                time_in_seconds = msg.time
                absolute_time += time_in_seconds
                self.message_queue.append((absolute_time, msg))
            self.message_queue.sort(key=lambda x: x[0])
            self.total_messages = len(self.message_queue)
            self.current_message_index = 0
            self.start_time = time.perf_counter()
            self.pause_offset = 0.0
            self.total_length = self.message_queue[-1][0] if self.message_queue else 0.0
            logging.info("MIDI messages prepared for playback.")
        except:
            logging.exception("Error preparing MIDI messages.")
            self.is_playing = False

    def get_total_length(self):
        return self.total_length

    def get_current_logical_time(self):
        if self.paused or self.paused_for_soundfont:
            return self.paused_logical_time
        if not self.is_playing and not self.paused and not self.paused_for_soundfont:
            return self.total_length
        current_real_time = time.perf_counter()
        return ((current_real_time - self.start_time) * self.playback_speed) - self.pause_offset

    def update(self):
        if self.interrupted or not self.is_playing or self.paused or self.paused_for_soundfont:
            return
        try:
            current_logical_time = self.get_current_logical_time()
            while self.current_message_index < self.total_messages:
                message_time, msg = self.message_queue[self.current_message_index]
                if current_logical_time >= message_time:
                    if not msg.is_meta:
                        channel = msg.channel if hasattr(msg, 'channel') else 0
                        if msg.type == 'note_on' and msg.velocity > 0:
                            midi_note = msg.note + (self.octave_shift * 12)
                            self.fs.noteon(channel, midi_note, msg.velocity)
                            self.active_notes.add((channel, msg.note))
                            self.global_active_notes.add(midi_note)
                        elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                            midi_note = msg.note + (self.octave_shift * 12)
                            self.fs.noteoff(channel, midi_note)
                            if (channel, msg.note) in self.active_notes:
                                self.active_notes.remove((channel, msg.note))
                            if midi_note in self.global_active_notes:
                                self.global_active_notes.remove(midi_note)
                        elif msg.type == 'program_change':
                            if channel != 9:
                                self.fs.program_change(channel, msg.program)
                    self.current_message_index += 1
                else:
                    break
            if self.current_message_index >= self.total_messages and not self.active_notes:
                if self.loop_mode and not self.interrupted:
                    self.current_message_index = 0
                    self.start_time = time.perf_counter()
                    self.pause_offset = 0.0
                else:
                    self.is_playing = False
        except:
            logging.exception("Error during MIDIPlayer update.")
            self.is_playing = False

    def stop(self):
        try:
            for note_info in list(self.active_notes):
                channel, orig_note = note_info
                adjusted_note = orig_note + (self.octave_shift * 12)
                self.fs.noteoff(channel, adjusted_note)
                self.active_notes.remove(note_info)
                self.global_active_notes.discard(adjusted_note)
            self.is_playing = False
            self.interrupted = True
        except:
            logging.exception("Error stopping MIDI playback.")

    def seek(self, seconds):
        try:
            current_time = self.get_current_logical_time()
            new_time = current_time + seconds
            new_time = max(0, min(new_time, self.total_length))
            for (channel, note) in list(self.active_notes):
                adjusted_note = note + (self.octave_shift * 12)
                self.fs.noteoff(channel, adjusted_note)
                self.global_active_notes.discard(adjusted_note)
                self.active_notes.remove((channel, note))
            idx = 0
            while idx < self.total_messages and self.message_queue[idx][0] <= new_time:
                idx += 1
            self.current_message_index = idx
            current_real_time = time.perf_counter()
            self.start_time = current_real_time - ((new_time + self.pause_offset) / self.playback_speed)
            if self.paused or self.paused_for_soundfont:
                self.paused_logical_time = new_time
        except:
            logging.exception("Error during seeking.")

    def set_octave_shift(self, new_shift):
        try:
            old_shift = self.octave_shift
            self.octave_shift = new_shift
            for (channel, note) in list(self.active_notes):
                old_midi = note + (old_shift * 12)
                self.fs.noteoff(channel, old_midi)
                self.global_active_notes.discard(old_midi)
                self.active_notes.remove((channel, note))
        except:
            logging.exception("Error changing octave shift.")

    def set_playback_speed(self, new_speed):
        try:
            current_logical_time = self.get_current_logical_time()
            self.playback_speed = new_speed
            self.start_time = time.perf_counter() - (current_logical_time / self.playback_speed)
            if self.paused or self.paused_for_soundfont:
                self.paused_logical_time = current_logical_time
        except:
            logging.exception("Error changing playback speed.")

    def toggle_pause(self):
        try:
            if self.paused:
                current_real_time = time.perf_counter()
                self.pause_offset += (current_real_time - self.pause_start) * self.playback_speed
                self.paused = False
            else:
                self.paused_logical_time = self.get_current_logical_time()
                self.pause_start = time.perf_counter()
                self.paused = True
                for (channel, note) in list(self.active_notes):
                    adjusted_note = note + (self.octave_shift * 12)
                    self.fs.noteoff(channel, adjusted_note)
                    self.global_active_notes.discard(adjusted_note)
                    self.active_notes.remove((channel, note))
        except:
            logging.exception("Error toggling pause.")

    def pause_for_soundfont_change(self):
        try:
            if not self.paused_for_soundfont:
                self.paused_logical_time = self.get_current_logical_time()
                self.pause_start = time.perf_counter()
                self.paused_for_soundfont = True
                for (channel, note) in list(self.active_notes):
                    adjusted_note = note + (self.octave_shift * 12)
                    self.fs.noteoff(channel, adjusted_note)
                    self.global_active_notes.discard(adjusted_note)
                    self.active_notes.remove((channel, note))
        except:
            logging.exception("Error pausing for SoundFont change.")

    def resume_after_soundfont_change(self):
        try:
            if self.paused_for_soundfont:
                current_real_time = time.perf_counter()
                self.pause_offset += (current_real_time - self.pause_start) * self.playback_speed
                self.paused_for_soundfont = False
        except:
            logging.exception("Error resuming after SoundFont change.")

class PianoApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.octave_shift = 0
        self.playback_speed = 1.0
        self.recording = []
        self.is_recording = False
        self.pressed_keys = {}
        self.key_to_midi_note = {}
        self.midi_mode = False
        self.midi_player = None
        self.loop_mode = False
        self.paused_for_soundfont = False
        self.operating_system = platform.system()
        self.fs = None
        self.selected_soundfont = None
        self.soundfont_id = None
        self.active_notes = set()
        self.initialize_ui_elements()
        self.ensure_soundfont()
        sf = self.initialize_fluidsynth()
        if sf is None:
            self.running = False
        else:
            self.running = True
        self.instructions = [
            "Pianomancer - Transform your keyboard into a piano!",
            "",
            "Instructions:",
            "Press the keys to play notes (see the virtual keyboard below).",
            "'R' to start/stop recording, 'P' to play recording.",
            "'1' to enter MIDI playback mode.",
            "'2' to change the SoundFont.",
            "'3' to toggle loop mode ON/OFF.",
            "'4' to play/pause current MIDI playback.",
            "'<' to seek backward 5s, '>' to seek forward 5s.",
            "'[' or ']' to decrease/increase the octave.",
            "'-' or '+' to decrease/increase playback speed.",
            "'Q' to quit, 'S' to stop MIDI playback.",
            "",
            "Virtual Keyboard:"
        ]
        self.tree_lines = [
            "        ★        ",
            "        *        ",
            "       ***       ",
            "      *O*O*      ",
            "     *******     ",
            "    *O*****O*    ",
            "   ***********   ",
            "  *O*********O*  ",
            "       ***       ",
            "       ***       "
        ]
        self.tree_display = ChristmasTreeDisplay(
            tree_lines=self.tree_lines,
            color_pairs=[curses.color_pair(1), curses.color_pair(2),
                         curses.color_pair(3), curses.color_pair(5),
                         curses.color_pair(6)],
            stdscr=self.stdscr
        )
        self.virtual_keyboard = ' '.join(NOTE_MIDI_NUMBERS.keys())

    def ensure_soundfont(self):
        if not os.path.exists("Arachno.sf2"):
            self.download_soundfont("https://theater.torbware.space/Arachno.sf2", "Arachno.sf2")

    def download_soundfont(self, url, filename):
        max_y, max_x = self.stdscr.getmaxyx()
        self.stdscr.erase()
        try:
            self.stdscr.addstr(max_y//2, max_x//2 - 15, "Downloading SoundFont...", curses.color_pair(7))
            self.stdscr.refresh()
        except:
            pass
        def report(block_num, block_size, total_size):
            downloaded = block_num * block_size
            perc = 0
            if total_size > 0:
                perc = downloaded / total_size * 100
            max_y, max_x = self.stdscr.getmaxyx()
            try:
                self.stdscr.move(max_y//2 + 1, max_x//2 - 20)
                self.stdscr.clrtoeol()
                bar_length = 30
                filled_length = int(bar_length * perc // 100)
                bar_str = "[" + ("█" * filled_length) + (" " * (bar_length - filled_length)) + "]"
                self.stdscr.addstr(max_y//2 + 1, max_x//2 - 20, f"{bar_str} {perc:5.1f}%")
                self.stdscr.refresh()
            except:
                pass
        urllib.request.urlretrieve(url, filename, reporthook=report)

    def initialize_fluidsynth(self):
        try:
            if self.operating_system == "Linux":
                driver = "alsa"
            elif self.operating_system == "Darwin":
                driver = "coreaudio"
            elif self.operating_system == "Windows":
                driver = "dsound"
            else:
                driver = "alsa"
            self.fs = fluidsynth.Synth()
            with SuppressStderr():
                try:
                    self.fs.start(driver=driver)
                except:
                    if driver != "alsa":
                        alternative_driver = "alsa"
                        self.fs.start(driver=alternative_driver)
                        driver = alternative_driver
                    else:
                        self.display_error("No audio driver available for FluidSynth.")
                        return None
            if not os.path.exists("Arachno.sf2"):
                self.display_error("Arachno.sf2 was not found.")
                return None
            new_sf = "Arachno.sf2"
            with SuppressStderr():
                try:
                    self.soundfont_id = self.fs.sfload(new_sf, True)
                    for channel in range(16):
                        self.fs.program_select(channel, self.soundfont_id, 0, 0)
                except:
                    self.display_error(f"Error loading SoundFont '{new_sf}'.")
                    return None
            return new_sf
        except:
            logging.exception("Error initializing FluidSynth.")
            self.display_error("Unexpected error initializing FluidSynth.")
            return None

    def initialize_ui_elements(self):
        try:
            curses.curs_set(0)
            self.stdscr.nodelay(True)
            curses.start_color()
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)
        except:
            pass

    def display_error(self, message):
        max_y, max_x = self.stdscr.getmaxyx()
        self.stdscr.erase()
        try:
            self.stdscr.addstr(max(max_y//2,0), max(max_x//2 - len(message)//2, 0), message, curses.color_pair(7))
            self.stdscr.refresh()
            self.stdscr.nodelay(False)
            self.stdscr.getch()
            self.stdscr.nodelay(True)
        except:
            pass

    def select_soundfont(self, soundfonts):
        selected = 0
        start_index = 0
        while True:
            max_y, max_x = self.stdscr.getmaxyx()
            if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
                draw_resize_prompt(self.stdscr, max_y, max_x)
                key = self.stdscr.getch()
                time.sleep(0.5)
                continue
            if len(soundfonts) == 0:
                return None
            if selected < start_index:
                start_index = selected
            visible_height = max_y - 6
            if visible_height < 1:
                time.sleep(0.5)
                continue
            if selected >= start_index + visible_height:
                start_index = selected - visible_height + 1
            display_scrollable_list(self.stdscr, soundfonts, selected, start_index, "Select a SoundFont (.sf2) to use:")
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(soundfonts)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(soundfonts)
            elif key == curses.KEY_PPAGE:
                selected = max(0, selected - visible_height)
            elif key == curses.KEY_NPAGE:
                selected = min(len(soundfonts) - 1, selected + visible_height)
            elif key in [10, 13]:
                return soundfonts[selected]
            elif key in [ord('q'), ord('Q')]:
                return None

    def select_midi_file(self, midi_files):
        selected = 0
        start_index = 0
        while True:
            max_y, max_x = self.stdscr.getmaxyx()
            if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
                draw_resize_prompt(self.stdscr, max_y, max_x)
                key = self.stdscr.getch()
                time.sleep(0.5)
                continue
            if len(midi_files) == 0:
                return None
            if selected < start_index:
                start_index = selected
            visible_height = max_y - 6
            if visible_height < 1:
                time.sleep(0.5)
                continue
            if selected >= start_index + visible_height:
                start_index = selected - visible_height + 1
            display_scrollable_list(self.stdscr, midi_files, selected, start_index, "Select a MIDI file to play:")
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(midi_files)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(midi_files)
            elif key == curses.KEY_PPAGE:
                selected = max(0, selected - visible_height)
            elif key == curses.KEY_NPAGE:
                selected = min(len(midi_files) - 1, selected + visible_height)
            elif key in [10, 13]:
                return midi_files[selected]
            elif key in [ord('q'), ord('Q')]:
                return None

    def play_recording(self):
        if not self.recording:
            self.display_error("No recording to play.")
            return
        playback_thread = threading.Thread(target=self.playback_thread, args=(self.recording,))
        playback_thread.start()

    def playback_thread(self, recording):
        if not recording:
            return
        start_time = recording[0][2]
        active_notes = set()
        last_event_time = start_time
        for event in recording:
            event_type, midi_note, event_time = event
            wait_time = (event_time - last_event_time) / self.playback_speed
            if wait_time > 0:
                time.sleep(wait_time)
            last_event_time = event_time
            adjusted_note = midi_note + (self.octave_shift * 12)
            if event_type == 'note_on':
                self.fs.noteon(0, adjusted_note, 127)
                active_notes.add(adjusted_note)
                self.active_notes.add(adjusted_note)
            elif event_type == 'note_off':
                self.fs.noteoff(0, adjusted_note)
                if adjusted_note in active_notes:
                    active_notes.remove(adjusted_note)
                if adjusted_note in self.active_notes:
                    self.active_notes.remove(adjusted_note)
        for note in active_notes:
            self.fs.noteoff(0, note)

    def run(self):
        if not self.running:
            return
        while True:
            try:
                max_y, max_x = self.stdscr.getmaxyx()
                if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
                    draw_resize_prompt(self.stdscr, max_y, max_x)
                    key = self.stdscr.getch()
                    time.sleep(0.5)
                    continue
                self.tree_display.active_notes = self.active_notes
                self.tree_display.update_display()
                start_line = self.tree_display.note_display_start_line + 2
                for idx, line in enumerate(self.instructions):
                    if start_line + idx >= max_y - 5:
                        break
                    self.stdscr.move(start_line + idx, 2)
                    self.stdscr.clrtoeol()
                    self.stdscr.addstr(start_line + idx, 2, line, curses.color_pair(7))
                kb_line = start_line + len(self.instructions)
                if kb_line < max_y:
                    self.stdscr.move(kb_line, 2)
                    self.stdscr.clrtoeol()
                    self.stdscr.addstr(kb_line, 2, self.virtual_keyboard, curses.color_pair(3))
                oct_line = kb_line + 1
                if oct_line < max_y:
                    self.stdscr.move(oct_line, 2)
                    self.stdscr.clrtoeol()
                    self.stdscr.addstr(oct_line, 2, f"Octave Shift: {self.octave_shift}", curses.color_pair(6))
                speed_line = kb_line + 2
                if speed_line < max_y:
                    self.stdscr.move(speed_line, 2)
                    self.stdscr.clrtoeol()
                    self.stdscr.addstr(speed_line, 2, f"Playback Speed: {self.playback_speed:.1f}x", curses.color_pair(6))
                loop_line = kb_line + 3
                if loop_line < max_y:
                    self.stdscr.move(loop_line, 2)
                    self.stdscr.clrtoeol()
                    loop_status = "ON" if self.loop_mode else "OFF"
                    self.stdscr.addstr(loop_line, 2, f"Loop Mode: {loop_status}", curses.color_pair(6))
                if self.is_recording:
                    rec_line = kb_line + 4
                    if rec_line < max_y:
                        self.stdscr.move(rec_line, 2)
                        self.stdscr.clrtoeol()
                        self.stdscr.addstr(rec_line, 2, "Recording... (Press 'R' to stop)", curses.color_pair(1))
                status_line = kb_line + 5 if not self.is_recording else kb_line + 6
                if self.midi_mode and self.midi_player and status_line < max_y:
                    self.stdscr.move(status_line, 2)
                    self.stdscr.clrtoeol()
                    if self.midi_player.paused:
                        pause_status = "Paused"
                    elif not self.midi_player.is_playing and not self.midi_player.paused and not self.midi_player.paused_for_soundfont:
                        pause_status = "Stopped"
                    else:
                        pause_status = "Playing"
                    self.stdscr.addstr(status_line, 2, f"MIDI Status: {pause_status}", curses.color_pair(7))
                self.stdscr.noutrefresh()
                if self.midi_mode and self.midi_player:
                    self.midi_player.update()
                    if not self.midi_player.is_playing and not self.midi_player.paused and not self.midi_player.paused_for_soundfont:
                        self.midi_mode = False
                if self.midi_mode and self.midi_player:
                    draw_progress_bar(self.stdscr, self.midi_player)
                curses.doupdate()
                try:
                    key = self.stdscr.getch()
                except:
                    key = -1
                current_time = time.perf_counter()
                if key != -1:
                    if key == curses.KEY_RESIZE:
                        handle_resize(self.stdscr)
                        continue
                    try:
                        key_char = chr(key).lower()
                    except ValueError:
                        key_char = ''
                    if key_char == 'q':
                        if self.midi_mode and self.midi_player:
                            self.midi_player.stop()
                            self.midi_mode = False
                        break
                    elif key_char == 's':
                        if self.midi_mode and self.midi_player:
                            self.midi_player.stop()
                            self.midi_mode = False
                    elif key_char == '[':
                        self.octave_shift -= 1
                        if self.midi_mode and self.midi_player:
                            self.midi_player.set_octave_shift(self.octave_shift)
                    elif key_char == ']':
                        self.octave_shift += 1
                        if self.midi_mode and self.midi_player:
                            self.midi_player.set_octave_shift(self.octave_shift)
                    elif key_char == '-':
                        new_speed = max(0.1, self.playback_speed - 0.1)
                        self.playback_speed = new_speed
                        if self.midi_mode and self.midi_player:
                            self.midi_player.set_playback_speed(new_speed)
                    elif key_char == '+':
                        new_speed = self.playback_speed + 0.1
                        self.playback_speed = new_speed
                        if self.midi_mode and self.midi_player:
                            self.midi_player.set_playback_speed(new_speed)
                    elif key_char == '3':
                        self.loop_mode = not self.loop_mode
                        if self.midi_mode and self.midi_player:
                            self.midi_player.loop_mode = self.loop_mode
                    elif key_char == '4':
                        if self.midi_mode and self.midi_player:
                            self.midi_player.toggle_pause()
                    elif key_char == '<':
                        if self.midi_mode and self.midi_player:
                            self.midi_player.seek(-5)
                    elif key_char == '>':
                        if self.midi_mode and self.midi_player:
                            self.midi_player.seek(5)
                    elif key_char == '2':
                        soundfonts = [f for f in os.listdir('.') if f.lower().endswith('.sf2')]
                        if not soundfonts:
                            self.display_error("No SoundFont (.sf2) files found.")
                            continue
                        if self.midi_mode and self.midi_player:
                            self.midi_player.pause_for_soundfont_change()
                        new_sf = self.select_soundfont(soundfonts)
                        self.stdscr.erase()
                        self.stdscr.refresh()
                        if new_sf:
                            with SuppressStderr():
                                try:
                                    self.soundfont_id = self.fs.sfload(new_sf, True)
                                    for channel in range(16):
                                        self.fs.program_select(channel, self.soundfont_id, 0, 0)
                                except:
                                    self.display_error(f"Error loading SoundFont '{new_sf}'.")
                            if self.midi_mode and self.midi_player:
                                self.midi_player.resume_after_soundfont_change()
                        else:
                            if self.midi_mode and self.midi_player:
                                self.midi_player.resume_after_soundfont_change()
                    else:
                        if not self.midi_mode:
                            if key_char in NOTE_MIDI_NUMBERS:
                                midi_note = NOTE_MIDI_NUMBERS[key_char] + (self.octave_shift * 12)
                                if key_char not in self.key_to_midi_note:
                                    self.fs.noteon(0, midi_note, 127)
                                    self.active_notes.add(midi_note)
                                    self.key_to_midi_note[key_char] = midi_note
                                self.pressed_keys[key_char] = current_time
                                if self.is_recording:
                                    self.recording.append(('note_on', midi_note, current_time))
                            elif key_char == 'r':
                                if not self.is_recording:
                                    self.recording = []
                                    self.is_recording = True
                                else:
                                    self.is_recording = False
                                    for midi_note in list(self.active_notes):
                                        self.recording.append(('note_off', midi_note, current_time))
                                        self.fs.noteoff(0, midi_note)
                                        self.active_notes.remove(midi_note)
                                    self.key_to_midi_note.clear()
                            elif key_char == 'p':
                                if self.recording:
                                    self.is_recording = False
                                    self.play_recording()
                                else:
                                    self.display_error("No recording to play.")
                            elif key_char == '1':
                                if self.midi_mode and self.midi_player:
                                    self.midi_player.stop()
                                    self.midi_mode = False
                                midi_files = [f for f in os.listdir('.') if f.lower().endswith(('.mid', '.midi'))]
                                if midi_files:
                                    selected_midi = self.select_midi_file(midi_files)
                                    self.stdscr.erase()
                                    self.stdscr.refresh()
                                    if selected_midi:
                                        self.midi_mode = True
                                        self.midi_player = MIDIPlayer(selected_midi, self.octave_shift, self.playback_speed, self.fs, self.active_notes, self.stdscr, self.loop_mode)
                                else:
                                    self.display_error("No MIDI files found.")
            except:
                self.display_error("An unexpected error occurred. Check the log.")
                break
            keys_to_stop = []
            for k_char, t in self.pressed_keys.items():
                if time.perf_counter() - t > 0.1:
                    keys_to_stop.append(k_char)
            for k_char in keys_to_stop:
                if k_char in self.key_to_midi_note:
                    midi_note = self.key_to_midi_note[k_char]
                    if self.is_recording:
                        self.recording.append(('note_off', midi_note, time.perf_counter()))
                    self.fs.noteoff(0, midi_note)
                    if midi_note in self.active_notes:
                        self.active_notes.remove(midi_note)
                    del self.key_to_midi_note[k_char]
                del self.pressed_keys[k_char]
            time.sleep(0.01)
        self.cleanup()

    def cleanup(self):
        try:
            if self.fs:
                self.fs.delete()
            curses.endwin()
        except:
            pass

def main(stdscr):
    app = PianoApp(stdscr)
    app.run()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except:
        logging.exception("Error in main application execution.")
        print("An error occurred. Check the pianomancer.log file for more details.")


