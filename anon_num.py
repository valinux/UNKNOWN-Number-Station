import numpy as np
import scipy.io.wavfile as wav
import argparse
import tkinter as tk
from tkinter import filedialog
import sys

# --- Parameters ---
SAMPLE_RATE = 19000         # Sampling rate in Hz
CARRIER_FREQS = [1000, 2000, 3000, 4000, 5000, 6000]  # Subcarrier frequencies (Hz)
SYMBOL_RATE = 50            # Baud rate (symbols per second)

# --- Helper Functions ---

def binary_to_bytes(binary_str):
    """Convert a string of binary digits into a bytes object.
       Assumes len(binary_str) is a multiple of 8.
    """
    return bytes(int(binary_str[i:i+8], 2) for i in range(0, len(binary_str), 8))

# --- Modulation / Demodulation Functions ---

def encode_rdft(binary_data):
    """
    Encode a string of '0's and '1's into a modulated waveform.
    A 32-bit header (payload length) is assumed to be prepended already.
    Each bit is represented by one symbol of duration 1/SYMBOL_RATE.
    The symbol’s carrier frequency is chosen from CARRIER_FREQS in a cyclic manner.
    A '1' is transmitted as a sine wave and a '0' as its inverted (negative) version.
    Returns a NumPy array of int16 samples.
    """
    samples_per_symbol = int(SAMPLE_RATE / SYMBOL_RATE)
    t_symbol = np.linspace(0, 1/SYMBOL_RATE, samples_per_symbol, endpoint=False)
    
    # Precompute sine waves for each carrier frequency.
    sine_waves = {f: np.sin(2 * np.pi * f * t_symbol) for f in CARRIER_FREQS}
    symbols = []
    
    for i, bit in enumerate(binary_data):
        freq = CARRIER_FREQS[i % len(CARRIER_FREQS)]
        # Use the precomputed sine wave.
        symbol_wave = sine_waves[freq]
        # Invert the phase for a '0'
        if bit == '0':
            symbol_wave = -symbol_wave
        symbols.append(symbol_wave)
    
    # Concatenate all symbols into one waveform.
    modulated_signal = np.concatenate(symbols)
    # Normalize and scale to 16-bit PCM range.
    if np.max(np.abs(modulated_signal)) != 0:
        modulated_signal = modulated_signal / np.max(np.abs(modulated_signal))
    modulated_signal_int16 = np.int16(modulated_signal * 32767)
    return modulated_signal_int16

def decode_rdft(wav_file):
    """
    Decode a WAV file containing the modulated binary data.
    Returns a string of '0's and '1's corresponding to the decoded bits.
    The first 32 decoded bits represent the payload length (in bits).
    """
    try:
        rate, data = wav.read(wav_file)
    except Exception as e:
        raise RuntimeError(f"Error reading WAV file: {e}")
    
    if rate != SAMPLE_RATE:
        print(f"Warning: expected sample rate {SAMPLE_RATE} Hz but got {rate} Hz", file=sys.stderr)
    
    samples_per_symbol = int(rate / SYMBOL_RATE)
    num_symbols = len(data) // samples_per_symbol
    t_symbol = np.linspace(0, 1/SYMBOL_RATE, samples_per_symbol, endpoint=False)
    
    decoded_bits = []
    # For each symbol, use the corresponding carrier frequency.
    for i in range(num_symbols):
        segment = data[i * samples_per_symbol:(i+1) * samples_per_symbol]
        freq = CARRIER_FREQS[i % len(CARRIER_FREQS)]
        expected_wave = np.sin(2 * np.pi * freq * t_symbol)
        # Compute the correlation (dot product) between the segment and the expected wave.
        corr = np.dot(segment, expected_wave)
        bit = '1' if corr >= 0 else '0'
        decoded_bits.append(bit)
    
    return ''.join(decoded_bits)

# --- File Conversion Functions ---

def file_to_binary(file_path):
    """
    Read a file in binary mode and convert its contents into a string of bits.
    Each byte is represented by 8 binary digits.
    """
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
    except Exception as e:
        raise RuntimeError(f"Error reading file '{file_path}': {e}")
    
    return ''.join(format(byte, '08b') for byte in file_bytes)

# --- GUI Functions ---

def browse_file():
    file_path = filedialog.askopenfilename(title="Select File to Transmit")
    if file_path:
        try:
            # Convert file to binary and prepend a 32-bit header indicating payload length.
            payload_binary = file_to_binary(file_path)
            header = format(len(payload_binary), '032b')
            binary_data = header + payload_binary
            modulated_signal = encode_rdft(binary_data)
            wav.write('rdft_transmission.wav', SAMPLE_RATE, modulated_signal)
            status_label.config(text='File transmitted: rdft_transmission.wav')
        except Exception as e:
            status_label.config(text=f'Error: {e}')

def browse_wav():
    file_path = filedialog.askopenfilename(title="Select WAV File to Decode", filetypes=[('WAV Files', '*.wav')])
    if file_path:
        try:
            decoded_binary = decode_rdft(file_path)
        except Exception as e:
            status_label.config(text=f'Error during decoding: {e}')
            return
        
        # Ensure there is at least a header.
        if len(decoded_binary) < 32:
            status_label.config(text='Decoded data too short to contain header.')
            return
        
        header = decoded_binary[:32]
        payload_length = int(header, 2)
        payload = decoded_binary[32:32+payload_length]
        
        if payload_length % 8 != 0:
            status_label.config(text='Payload length is not a multiple of 8.')
            return
        
        try:
            output_bytes = binary_to_bytes(payload)
            with open('decoded_output.txt', 'wb') as f:
                f.write(output_bytes)
            status_label.config(text='File decoded: decoded_output.txt')
        except Exception as e:
            status_label.config(text=f'Error writing output file: {e}')

# --- Main Program with CLI/GUI support ---

def main():
    parser = argparse.ArgumentParser(description="RDFT File Transfer: Encode a file to a WAV and decode a WAV back to a file.")
    parser.add_argument('--encode', type=str, help="Path to the file to encode (transmit)")
    parser.add_argument('--decode', type=str, help="Path to the WAV file to decode")
    args = parser.parse_args()
    
    if args.encode:
        # Command-line encoding mode.
        try:
            payload_binary = file_to_binary(args.encode)
        except Exception as e:
            print(f"Error: {e}")
            return
        
        header = format(len(payload_binary), '032b')
        binary_data = header + payload_binary
        
        try:
            modulated_signal = encode_rdft(binary_data)
            wav.write('rdft_transmission.wav', SAMPLE_RATE, modulated_signal)
            print("File transmitted: rdft_transmission.wav")
        except Exception as e:
            print(f"Error during encoding/writing: {e}")
    
    elif args.decode:
        # Command-line decoding mode.
        try:
            decoded_binary = decode_rdft(args.decode)
        except Exception as e:
            print(f"Error during decoding: {e}")
            return
        
        if len(decoded_binary) < 32:
            print("Decoded data too short to contain header.")
            return
        
        header = decoded_binary[:32]
        payload_length = int(header, 2)
        payload = decoded_binary[32:32+payload_length]
        
        if payload_length % 8 != 0:
            print("Payload length is not a multiple of 8.")
            return
        
        try:
            output_bytes = binary_to_bytes(payload)
            with open('decoded_output.txt', 'wb') as f:
                f.write(output_bytes)
            print("File decoded: decoded_output.txt")
        except Exception as e:
            print(f"Error writing output file: {e}")
    
    else:
        # Launch GUI if no command-line arguments provided.
        global status_label
        root = tk.Tk()
        root.title("Unknown Number Station")
        
        transmit_button = tk.Button(root, text="Select File to Transmit", command=browse_file)
        decode_button = tk.Button(root, text="Select WAV to Decode", command=browse_wav)
        status_label = tk.Label(root, text="")
        
        transmit_button.pack(pady=10)
        decode_button.pack(pady=10)
        status_label.pack(pady=10)
        
        root.mainloop()

if __name__ == '__main__':
    main()

