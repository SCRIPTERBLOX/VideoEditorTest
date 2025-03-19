import math

import pygame

import struct
import zlib

def read_png(filename):
    """Reads a PNG file from scratch and extracts basic information."""

    with open(filename, 'rb') as f:
        # 1. Check the PNG Signature
        signature = f.read(8)
        if signature != b'\x89PNG\r\n\x1a\n':  # Standard PNG signature
            raise ValueError("Invalid PNG signature")

        # 2. Read Chunks
        chunks = []
        while True:
            length_bytes = f.read(4)
            if not length_bytes:
                break  # End of file

            length = struct.unpack('>I', length_bytes)[0]  # Big-endian unsigned int

            chunk_type = f.read(4).decode('ascii')  # Chunk type as ASCII string
            chunk_data = f.read(length)
            crc_bytes = f.read(4)
            crc = struct.unpack('>I', crc_bytes)[0]

            chunks.append((chunk_type, chunk_data, crc))

            # Optional: Validate CRC (not implemented here for brevity)
            # You'd need to implement the CRC algorithm and compare the calculated CRC
            # with the read CRC.


        # 3. Process Chunks
        width = None
        height = None
        color_type = None
        bit_depth = None
        image_data = b''

        for chunk_type, chunk_data, crc in chunks:
            if chunk_type == 'IHDR':
                width = struct.unpack('>I', chunk_data[0:4])[0]
                height = struct.unpack('>I', chunk_data[4:8])[0]
                bit_depth = chunk_data[8]
                color_type = chunk_data[9]


            elif chunk_type == 'IDAT':
                image_data += chunk_data
            elif chunk_type == 'IEND':
                pass # End of Image

        # 4. Decompress Image Data (if needed)
        try:
            decompressed_data = zlib.decompress(image_data)
        except zlib.error as e:
            raise ValueError(f"Error decompressing image data: {e}")


        # Now, you'll have 'decompressed_data' containing the raw pixel data.
        # The format of this data depends on the color_type and bit_depth.
        # Further processing is required to convert this data into a usable pixel array.


        return {
            'width': width,
            'height': height,
            'color_type': color_type,
            'bit_depth': bit_depth,
            'decompressed_data': decompressed_data
        }

# Example Usage:
try:
    png_info = read_png('/home/scripterblox/Desktop/SCRIPTERBLOX/OtherProjects/VideoEditor/PNGReader/src/channels_profile.png')  # Replace with your PNG file
    print(f"Width: {png_info['width']}")
    print(f"Height: {png_info['height']}")
    print(f"Color Type: {png_info['color_type']}")
    print(f"Bit Depth: {png_info['bit_depth']}")
    # Now you need to process the decompressed_data according to the color_type and bit depth.

    pygame.init()

    # Create the screen
    screen = pygame.display.set_mode((png_info['width'], png_info['height']))
    pygame.display.set_caption("PNG reader test")

    # Clock for controlling the frame rate
    clock = pygame.time.Clock()

    width = png_info['width'] # Just to get it into a more accesible variable
    height = png_info['height'] # Just to get it into a more accesible variable
    data = png_info['decompressed_data'] # Just to get it into a more accesible variable

    pixels = [] # list of pixels in the image
    for i in range(0, len(data), 3): # loop that increases by 3 (mabey 4) per iteration
        r = data[i] # e.g. loop I
        g = data[i+1] # e.g. loop I+1
        b = data[i+2] # e.g. loop I+2
        pixels.append((r, g, b)) # add this info into one color value

    with open("data.txt", "w") as f:  # Open file in write mode
        for item in data:
            f.write(str(item) + "\n")

    lastPixel = ()
    lastPixelOccurances = 0
    for pixel in pixels:
        if pixel == lastPixel:
            lastPixelOccurances += 1
        else:
            print(str(lastPixel)+", "+str(lastPixelOccurances))
            lastPixel = pixel
            lastPixelOccurances = 1


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
            color = pixels[pixelI] # that was surprisingly simpel

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
except ValueError as e:
    print(f"Error: {e}")
except FileNotFoundError:
    print("Error: File not found.")