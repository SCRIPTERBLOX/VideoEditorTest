import math

import pygame

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
            - bit_depth (int): The bit depth of the image.
            - pixel_data (bytes):  The raw, unfiltered pixel data.
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

                # 3. Process the chunk data based on its type
                if chunk_type_str == 'IHDR':
                    # Image Header
                    width, height, bit_depth, color_type, compression_method, filter_method, interlace_method = struct.unpack('>IIBBBBB', chunk_data)
                    print(f"Width: {width}, Height: {height}, Color Type: {color_type}, Bit Depth: {bit_depth}")

                elif chunk_type_str == 'IDAT':
                    # Image Data
                    pixel_data += chunk_data

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

            #Apply Filters to image data
            scanline_length = width * 3 + 1
            unfiltered_data = apply_filters_to_data(width, height, decompressed_data)

            return width, height, color_type, bit_depth, unfiltered_data

    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def apply_sub_filter(scanline_data, width):
    """Applies the 'Sub' filter (filter_type=1) to a scanline."""
    filtered_scanline = bytearray(scanline_data)
    bytes_per_pixel = 3  # RGB, 8-bit
    for i in range(bytes_per_pixel, len(scanline_data)):
        filtered_scanline[i] = (scanline_data[i] + filtered_scanline[i - bytes_per_pixel]) & 0xFF
    return bytes(filtered_scanline)

def apply_up_filter(scanline_data, width, previous_scanline_data):
    """Applies the 'Up' filter (filter_type=2) to a scanline."""
    filtered_scanline = bytearray(scanline_data)
    bytes_per_pixel = 3  # RGB, 8-bit

    if previous_scanline_data is None:
        # If there's no previous scanline (first line), treat it as all zeros
        return scanline_data

    for i in range(len(scanline_data)):
        filtered_scanline[i] = (scanline_data[i] + previous_scanline_data[i]) & 0xFF

    return bytes(filtered_scanline)

def apply_average_filter(scanline_data, width, previous_scanline_data, bytes_per_pixel):
    """Applies the 'Average' filter (filter_type=3) to a scanline."""
    filtered_scanline = bytearray(scanline_data)

    for i in range(len(scanline_data)):
        a = 0  # Left pixel
        b = 0  # Above pixel

        # Check the boundary conditions
        if i >= bytes_per_pixel:
            a = filtered_scanline[i - bytes_per_pixel]  # Pixel to the left
        if previous_scanline_data:
            b = previous_scanline_data[i]  # Pixel above

        # Calculate the average
        avg = (a + b) // 2  # Integer division
        filtered_scanline[i] = (scanline_data[i] + avg) & 0xFF

    return bytes(filtered_scanline)

def paeth_predictor(a, b, c):
    """Paeth predictor function."""
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)

    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c

def apply_paeth_filter(scanline_data, width, previous_scanline_data, bytes_per_pixel):
    """Applies the 'Paeth' filter (filter_type=4) to a scanline."""
    filtered_scanline = bytearray(scanline_data)

    for i in range(len(scanline_data)):
        a = 0  # Left pixel
        b = 0  # Above pixel
        c = 0  # Upper-left pixel

        # Check boundary conditions for 'a' (left)
        if i >= bytes_per_pixel:
            a = filtered_scanline[i - bytes_per_pixel]

        # Check boundary conditions for 'b' (above)
        if previous_scanline_data:
            b = previous_scanline_data[i]

        # Check boundary conditions for 'c' (upper-left)
        if previous_scanline_data and i >= bytes_per_pixel:
            c = previous_scanline_data[i - bytes_per_pixel]

        # Apply the Paeth predictor
        paeth = paeth_predictor(a, b, c)
        filtered_scanline[i] = (scanline_data[i] + paeth) & 0xFF

    return bytes(filtered_scanline)

def apply_filters_to_data(width, height, pixel_data):
    """Apply the correct PNG filters to the scanline data."""
    scanline_length = width * 3 + 1
    bytes_per_pixel = 3  #Assuming color type 2 with 8 bits.
    unfiltered_data = bytearray()
    previous_scanline = None  # Added to store the previous scanline for "Up" filter

    for row in range(height):
        filter_type = pixel_data[row * scanline_length]
        scanline = pixel_data[row * scanline_length + 1:(row + 1) * scanline_length]

        if filter_type == 0:
            unfiltered_data.extend(scanline)
            previous_scanline = scanline  #Keep track of last used scanline
        elif filter_type == 1:
            unfiltered_data.extend(apply_sub_filter(scanline, width))
            previous_scanline = scanline  #Keep track of last used scanline
        elif filter_type == 2:
            unfiltered_data.extend(apply_up_filter(scanline, width, previous_scanline))
            previous_scanline = scanline  #Keep track of last used scanline
        elif filter_type == 3:
            unfiltered_data.extend(apply_average_filter(scanline, width, previous_scanline, bytes_per_pixel))
            previous_scanline = scanline
        elif filter_type == 4:
            unfiltered_data.extend(apply_paeth_filter(scanline, width, previous_scanline, bytes_per_pixel))
            previous_scanline = scanline

        else:
            print(f"Unsupported filter {filter_type}")

    return bytes(unfiltered_data)

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
    if len(pixel_data) != width * height * 3:
        print("Error: Pixel data size is incorrect for RGB 8-bit.")
        return None

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
        width, height, color_type, bit_depth, pixel_data = result
        print(f"Successfully read PNG file: {png_file}")
        print(f"Width: {width}, Height: {height}, Color Type: {color_type}, Bit Depth: {bit_depth}")
        print(f"Length of pixel data: {len(pixel_data)} bytes")

        if color_type == 2 and bit_depth == 8:
            pixel_values = interpret_rgb_8bit(width, height, pixel_data)
            if pixel_values:
                print(f"First few pixel values (RGB 8-bit): {pixel_values[:10]}")  # Print the first 10 pixels

                pygame.init()

                # Create the screen
                screen = pygame.display.set_mode((width, height))
                pygame.display.set_caption("PNG reader test")

                # Clock for controlling the frame rate
                clock = pygame.time.Clock()

                # Main game loop
                running = True
                while running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False


                    # Fill the screen with the current color
                    screen.fill((0, 0, 0))

                    # now go through the gotten pixels and draw them to the screen
                    for pixelI in range(width*height):
                        # only info given is image width and height and pixel col for pixel index
                        # get the pixel index
                        color = pixel_values[pixelI] # that was surprisingly simpel

                        #assuming 10 x 10:
                        # i 9 / 10 = 0.9 | 0.9 < 1 => i 9 = y 1
                        # i 59 / 10 = 5.9 | 5.9

                        # procedure:
                        # 1. divide by width
                        # 2. get closest upwards int
                        # 3. thats the height value
                        # 4. multiply height value by width
                        # 5. remove that from the original value
                        # 6. thats the horizontal value

                        x = pixelI / width # 1.
                        y = math.ceil(x) # 2.
                        yPos = y # 3.
                        z = y*width # 4.
                        xz = pixelI-z # 5.
                        xPos = xz # 6.

                        # well does this work?

                        pygame.draw.line(screen, color, [xPos, yPos], [xPos, yPos], 1)


                    # Update the display
                    pygame.display.flip()

                    # Cap the frame rate
                    clock.tick(60)

                # Quit pygame
                pygame.quit()

        else:
            print("Image is not Truecolor RGB 8-bit, or the color type is not yet supported.")


    else:
        print(f"Failed to read PNG file: {png_file}")