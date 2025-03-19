import struct

def read_uint32(file_handle):
    """Reads a 32-bit unsigned integer from the file."""
    return struct.unpack(">I", file_handle.read(4))[0]

def read_box_header(file_handle):
    """Reads the size and type of a box."""
    size = read_uint32(file_handle)
    type_ = file_handle.read(4).decode('utf-8')
    return size, type_

def parse_mp4(file_path):
    with open(file_path, "rb") as f:
        while True:
            try:
                size, type_ = read_box_header(f)
                print(f"Found box: Type={type_}, Size={size}")

                if type_ == 'ftyp':
                    # Read ftyp data (brand information)
                    f.seek(size - 8, 1) # Skip the rest of the ftyp box

                elif type_ == 'moov':
                    # Parse the moov box recursively
                    parse_moov(f, size - 8)  #Remaining size after reading the header

                elif type_ == 'mdat':
                    # We don't parse mdat here, just skip it
                    f.seek(size - 8, 1)
                    print("Skipping mdat box")

                else:
                    # Skip unknown boxes
                    f.seek(size - 8, 1)  #seek relative to the current position.
                    print(f"Skipping unknown box: {type_}")

            except struct.error:
                # End of file
                break
            except Exception as e:
                print(f"Error processing file: {e}")
                break


def parse_moov(file_handle, moov_size):
    end_position = file_handle.tell() + moov_size
    while file_handle.tell() < end_position:
        size, type_ = read_box_header(file_handle)
        print(f"  Found box inside moov: Type={type_}, Size={size}")

        if type_ == 'mvhd':
            #parse movie header if you need it
            file_handle.seek(size - 8, 1) # Skip it for now

        elif type_ == 'trak':
            parse_trak(file_handle, size - 8)
        else:
            file_handle.seek(size - 8, 1)


def parse_trak(file_handle, trak_size):
    end_position = file_handle.tell() + trak_size
    while file_handle.tell() < end_position:
        size, type_ = read_box_header(file_handle)
        print(f"    Found box inside trak: Type={type_}, Size={size}")

        if type_ == 'tkhd':
            file_handle.seek(size - 8, 1)

        elif type_ == 'mdia':
            parse_mdia(file_handle, size - 8)
        else:
            file_handle.seek(size-8, 1)

def parse_mdia(file_handle, mdia_size):
    end_position = file_handle.tell() + mdia_size

    while file_handle.tell() < end_position:
        size, type_ = read_box_header(file_handle)
        print(f"      Found box inside mdia: Type={type_}, Size={size}")

        if type_ == 'mdhd':
            file_handle.seek(size-8, 1)
        elif type_ == 'hdlr':
            handler_type = file_handle.read(4).decode('utf-8') # Handler type is at byte 8.
            print("Handler Type: ", handler_type)
            file_handle.seek(size-12, 1)

        elif type_ == 'minf':
            parse_minf(file_handle, size - 8)
        else:
            file_handle.seek(size - 8, 1)

def parse_minf(file_handle, minf_size):
    end_position = file_handle.tell() + minf_size
    while file_handle.tell() < end_position:
        size, type_ = read_box_header(file_handle)
        print(f"        Found box inside minf: Type={type_}, Size={size}")

        if type_ == 'vmhd' or type_ == 'smhd':
            file_handle.seek(size - 8, 1)
        elif type_ == 'dinf':
            file_handle.seek(size - 8, 1)
        elif type_ == 'stbl':
            parse_stbl(file_handle, size - 8)

        else:
            file_handle.seek(size - 8, 1)


def parse_stbl(file_handle, stbl_size):
    end_position = file_handle.tell() + stbl_size

    while file_handle.tell() < end_position:
        size, type_ = read_box_header(file_handle)
        print(f"          Found box inside stbl: Type={type_}, Size={size}")

        if type_ == 'stsd':
            parse_stsd(file_handle, size -8 )
        elif type_ == 'stts':
            # Time to Sample
            file_handle.seek(size - 8, 1)

        elif type_ == 'stsc':
            # Sample to Chunk
            file_handle.seek(size - 8, 1)

        elif type_ == 'stsz':
            # Sample Size
            file_handle.seek(size - 8, 1)

        elif type_ == 'stco' or type_ == 'co64':
            # Chunk Offset
            file_handle.seek(size - 8, 1)
        else:
            file_handle.seek(size - 8, 1)

def parse_stsd(file_handle, stsd_size):
    end_position = file_handle.tell() + stsd_size
    file_handle.seek(4, 1) # skip version and flags (4 bytes)

    entry_count = read_uint32(file_handle) # Count of sample descriptions
    print("Entry Count: ", entry_count)

    for i in range(entry_count):
        size, type_ = read_box_header(file_handle)
        print(f"           Found box inside stsd: Type={type_}, Size={size}")

        if type_ == 'avc1': #H.264 video
            file_handle.seek(size - 8, 1) #skip avc1
        elif type_ == 'mp4a': #AAC audio
            file_handle.seek(size - 8, 1)
        else:
            file_handle.seek(size - 8, 1)


if __name__ == "__main__":
    mp4_file_path = "/home/scripterblox/Desktop/SCRIPTERBLOX/OtherProjects/VideoEditor/src/videos/2025-03-19 16-59-48.mp4"  # Replace with your file
    parse_mp4(mp4_file_path)