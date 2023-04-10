import librosa
import numpy as np
from pydub import AudioSegment
from music21 import stream, note, tempo, duration, meter


class MusicTranscriber:
    def __init__(self):
        # Set sample rate, n_fft (the length of the windowed signal after padding with zeros), and hop_length (the number of samples between successive frames)
        self.sample_rate = 22050
        self.n_fft = 2048
        self.hop_length = 512

    @staticmethod
    def is_valid_music_file(file_path):
        # Check if the file is a valid audio file by trying to read it with the AudioSegment library
        try:
            AudioSegment.from_file(file_path)
            return True
        except:
            return False

    def process_music_file(self, file_path):
        y, sr = librosa.load(file_path, sr=self.sample_rate)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, hop_length=self.hop_length)

        music_tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)

        onset_frames = librosa.time_to_frames(onsets, sr=sr, hop_length=self.hop_length)

        notes = []
        durations = []
        for idx, frame in enumerate(onset_frames):
            limited_frame = min(frame, magnitudes.shape[1] - 1)
            pitch_index = np.argmax(magnitudes[:, limited_frame])
            pitch = pitches[pitch_index, limited_frame]
            midi_note = librosa.hz_to_midi(pitch)

            if idx < len(onset_frames) - 1:
                next_frame = onset_frames[idx + 1]
            else:
                next_frame = len(y) // self.hop_length

            duration_note = max(0, (next_frame - frame) * self.hop_length / sr)
            durations.append(duration_note)
            notes.append((midi_note, duration_note))

        # Normalize durations
        max_allowed_duration = 4  # maximum allowed duration in quarter notes
        max_duration = max(durations)
        if max_duration > max_allowed_duration:
            factor = max_allowed_duration / max_duration
            for idx, (midi_note, duration_note) in enumerate(notes):
                notes[idx] = (midi_note, duration_note * factor)

        return notes, music_tempo

    @staticmethod
    def round_to_nearest_duration(duration_quarter_notes):
        possible_durations = [1 / 32, 1 / 16, 1 / 8, 1 / 4, 1 / 2, 1, 2, 4]

        # Find the nearest representable duration
        nearest_duration = min(possible_durations, key=lambda x: abs(x - duration_quarter_notes))

        # Check if the duration is less than the minimum value
        if nearest_duration < 1 / 32:
            return 1 / 32  # set the duration to the minimum value
        else:
            return nearest_duration

    def generate_music_xml(self, notes_and_durations, input_tempo, output_file_name, ticks_per_quarter=480):
        # Initialize a music21 stream
        music_stream = stream.Stream()

        # Create a TimeSignature object and set the ticks per quarter note (divisions)
        time_signature = meter.TimeSignature("4/4")
        time_signature.ticksPerQuarterNote = ticks_per_quarter

        # Add the TimeSignature object to the stream
        music_stream.append(time_signature)

        # Add tempo to the stream
        metronome = tempo.MetronomeMark(number=input_tempo)
        music_stream.append(metronome)

        # Calculate the duration of a quarter note in seconds
        quarter_duration_seconds = 60 / input_tempo

        # Calculate the number of ticks per second
        ticks_per_second = ticks_per_quarter * (1 / quarter_duration_seconds)

        # Calculate the duration of one measure in seconds
        measure_duration_seconds = time_signature.barDuration.quarterLength * quarter_duration_seconds

        current_measure = stream.Measure()
        current_measure_duration = 0

        # Add each note with its duration to the music21 stream
        for midi_note, note_duration in notes_and_durations:
            new_note = note.Note(midi=midi_note)

            # Convert duration in seconds to ticks
            duration_ticks = note_duration * ticks_per_second

            # Convert ticks to quarter notes
            duration_quarter_notes = duration_ticks / ticks_per_quarter

            # Round duration to the nearest representable value
            rounded_duration = self.round_to_nearest_duration(duration_quarter_notes)

            # Create Duration object
            new_note.duration = duration.Duration(rounded_duration)

            # Check if adding the note to the current measure would exceed the measure's duration
            if current_measure_duration + new_note.duration.quarterLength > measure_duration_seconds:
                # Fill the remaining duration in the measure with a rest
                rest_duration = measure_duration_seconds - current_measure_duration
                rounded_rest_duration = self.round_to_nearest_duration(rest_duration)  # Round rest_duration
                rest = note.Rest(quarterLength=rounded_rest_duration)
                current_measure.append(rest)

                # Add the current measure to the stream and start a new measure
                music_stream.append(current_measure)
                current_measure = stream.Measure()
                current_measure_duration = 0

            current_measure.append(new_note)
            current_measure_duration += new_note.duration.quarterLength

        # Add the last measure to the stream
        if current_measure:
            music_stream.append(current_measure)

        # Quantize the stream before writing to MusicXML
        quantized_stream = music_stream.quantize()

        # Write the music21 stream to a MusicXML file
        quantized_stream.write('musicxml', fp=output_file_name)

    def transcribe(self, file_path, output_file_name):
        # Check if the file is a valid music file
        if not self.is_valid_music_file(file_path):
            raise Exception("Invalid music file.")

        # Process the music file to get a list of notes and their durations, and the tempo
        notes_and_durations, music_tempo = self.process_music_file(file_path)

        # Generate a MusicXML file using the list of notes and durations and the tempo
        self.generate_music_xml(notes_and_durations, music_tempo, output_file_name)
