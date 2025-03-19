import struct
import zlib

def read_png(filename):
    """
    Reads a PNG file and extracts its basic information and pixel data
    without using external libraries beyond standard Python.

    Args:
        filename (str): The path to the PNG file.

    Returns:
        tuple: A tuple containing:
            - width (int): The width of the image.
            - height (int): The height of the image.
            - color_type (int): The color type (e.g., 0: grayscale, 2: truecolor, 3: indexed, 4: grayscale with alpha, 6: truecolor with alpha).
            - pixel_data (bytes):  The raw, unfiltered, and uncompressed pixel data.
            - palette (list of tuples):  The palette if the color_type is 3, otherwise None.

        Returns None if there's an error reading the file.

    """

    try:
        with open(filename, 'rb') as f:
            # 1. Check the PNG signature
            signature = f.read(8)
            if signature != b'\x89PNG\r\n\x1a\n':
                print("Error: Invalid PNG signature.")
                return None

            width = None
            height = None
            color_type = None
            bit_depth = None
            compression_method = None
            filter_method = None
            interlace_method = None
            pixel_data = b""
            palette = []


            # 2. Read chunks until IEND
            while True:
                # Read the length of the chunk (4 bytes, big-endian)
                length_bytes = f.read(4)
                if len(length_bytes) != 4:
                    print("Error: Unexpected end of file while reading chunk length.")
                    return None
                length = struct.unpack('>I', length_bytes)[0]

                # Read the chunk type (4 bytes)
                chunk_type = f.read(4)
                if len(chunk_type) != 4:
                    print("Error: Unexpected end of file while reading chunk type.")
                    return None
                chunk_type_str = chunk_type.decode('ascii')


                # Read the chunk data
                chunk_data = f.read(length)
                if len(chunk_data) != length:
                    print(f"Error: Expected {length} bytes for chunk data, but got {len(chunk_data)}.")
                    return None

                # Read the CRC (4 bytes)
                crc_bytes = f.read(4)
                if len(crc_bytes) != 4:
                    print("Error: Unexpected end of file while reading CRC.")
                    return None
                # TODO: Verify the CRC (optional for this example, but important!)
                # crc = struct.unpack('>I', crc_bytes)[0]
                # Implement CRC-32 calculation here for verification.


                # 3. Process the chunk data based on its type
                if chunk_type_str == 'IHDR':
                    # Image Header
                    width, height, bit_depth, color_type, compression_method, filter_method, interlace_method = struct.unpack('>IIBBBBB', chunk_data)
                    print(f"Width: {width}, Height: {height}, Color Type: {color_type}, Bit Depth: {bit_depth}")


                elif chunk_type_str == 'IDAT':
                    # Image Data
                    pixel_data += chunk_data

                elif chunk_type_str == 'PLTE':
                    # Palette data (for indexed color images)
                    for i in range(0, len(chunk_data), 3):
                        palette.append((chunk_data[i], chunk_data[i+1], chunk_data[i+2])) # R,G,B

                elif chunk_type_str == 'IEND':
                    # Image Trailer (end of file)
                    break  # Exit the loop

                else:
                    # Ignore ancillary chunks (optional)
                    print(f"Ignoring chunk type: {chunk_type_str}")
                    pass  # You can add handling for other chunk types if needed



            # 4. Decompress the pixel data
            try:
                decompressed_data = zlib.decompress(pixel_data)
            except zlib.error as e:
                print(f"Error during zlib decompression: {e}")
                return None



            return width, height, color_type, decompressed_data, palette

    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def interpret_rgb_8bit(width, height, pixel_data):
    """
    Interprets pixel data for Truecolor RGB with 8-bit depth.

    Args:
        width (int): The width of the image.
        height (int): The height of the image.
        pixel_data (bytes): The pixel data (decompressed and unfiltered).

    Returns:
        list: A list of tuples, where each tuple represents a pixel (R, G, B). Returns None on error.
    """
    #if len(pixel_data) != width * height * 3:
    #    print("Error: Pixel data size is incorrect for RGB 8-bit.")
    #    return None

    pixels = []
    for i in range(0, len(pixel_data), 3):
        r = pixel_data[i]
        g = pixel_data[i + 1]
        b = pixel_data[i + 2]
        pixels.append((r, g, b))

    return pixels

# Example usage
if __name__ == "__main__":
    png_file = "/home/scripterblox/Desktop/SCRIPTERBLOX/OtherProjects/VideoEditor/PNGReader/src/channels_profile.png"  # Replace with your PNG file name

    result = read_png(png_file)

    if result:
        width, height, color_type, pixel_data, palette = result
        print(f"Successfully read PNG file: {png_file}")
        print(f"Width: {width}, Height: {height}, Color Type: {color_type}")
        print(f"Length of pixel data: {len(pixel_data)} bytes")

        print(pixel_data[0])

        if color_type == 2:
            pixels = interpret_rgb_8bit(width, height, pixel_data)

            print(pixels)

        # Process the pixel data further (e.g., apply filtering if needed, interpret pixel values)
        # This part depends heavily on the color type, bit depth, and interlace method of the PNG.

        if color_type == 3:
            print(f"Palette size: {len(palette)}")
        #Example of writing pixel data to a raw file for debugging or processing.
        #with open("output.raw", "wb") as f:
        #    f.write(pixel_data)



    else:
        print(f"Failed to read PNG file: {png_file}")