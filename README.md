# Unknown Number Station

This repository contains a Python script for encoding and decoding files using audio modulation.  It converts files into WAV audio files by representing each bit as a sine wave symbol with varying carrier frequencies.

## How It Works

### Encoding a File:

1.  The input file is read in binary mode.
2.  Each byte is converted to its 8-bit binary representation.
3.  A 32-bit header (storing the payload length in bits) is prepended to the binary data.
4.  Each bit (from the header and payload) is modulated into a sine wave symbol. The carrier frequency for a symbol is selected by cycling through a predefined list of carrier frequencies (`CARRIER_FREQS`).
5.  The resulting waveform is normalized.
6.  The normalized waveform is written as a 16-bit PCM WAV file named `rdft_transmission.wav`.

### Decoding a WAV:

1.  The WAV file (`rdft_transmission.wav`) is read and split into individual symbols.
2.  For each symbol, the corresponding carrier frequency (used during encoding) is regenerated.
3.  The regenerated carrier frequency is used to correlate with the received signal (the symbol).
4.  The sign of the correlation result determines whether the bit is a "1" or a "0".
5.  The first 32 decoded bits are interpreted as the payload length (in bits).
6.  The subsequent bits (according to the payload length) are grouped into 8-bit chunks.
7.  Each 8-bit chunk is converted back into a byte.
8.  The decoded bytes are written to a file named `decoded_output.txt`.

## Usage Modes

The script can be used in two modes:

### GUI Mode

Run the script without any command-line arguments to use the simple Tkinter graphical interface. This interface provides a user-friendly way to select files for encoding and decoding.

```bash
python anon_num.py 
```

### CLI Mode

Use command-line arguments to process files directly.

**Encoding:**

```bash
python anon_num.py --encode <file>
```

Replace `<file>` with the path to the file you want to encode.

**Decoding:**

```bash
python anon_num.py --decode <wav>
```

Replace `<wav>` with the path to the WAV file you want to decode (typically `rdft_transmission.wav`).

## Dependencies

Make sure you have the following Python libraries installed:

*   `wave` (or `pyaudio` for more advanced audio handling)
*   `numpy`
*   `scipy`
*   `tkinter` (for the GUI mode)

You can install them using pip:

```bash
pip install wave numpy scipy
```

(tkinter is usually included with Python)

## Example

**Encoding:**

```bash
python anon_num.py --encode my_document.txt
```

This will create `rdft_transmission.wav`.

**Decoding:**

```bash
python anon_num.py --decode rdft_transmission.wav
```

This will create `decoded_output.txt` containing the decoded content of `my_document.txt`.

## Notes

*   The quality of the audio and the success of the decoding depend on the chosen carrier frequencies, the sample rate, and other audio parameters.  These are likely defined as constants within the script.
*   Error handling and input validation could be improved for more robust operation.

## Contributing

Contributions are welcome!  Please feel free to submit pull requests or open issues.
