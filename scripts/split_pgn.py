import os
import zstandard as zstd
import io
import time

def split_pgn(input_file, output_dir, max_chunk_size_bytes=120_000_000): # 120 MB
    print(f"Starting splitting process for {input_file}...")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    dctx = zstd.ZstdDecompressor()
    
    chunk_index = 1
    current_size = 0
    start_time = time.time()
    
    out_f = None
    
    def open_new_chunk(idx):
        filename = os.path.join(output_dir, f"chunk_{idx:03d}.pgn")
        print(f"Opening new chunk: {filename}")
        return open(filename, "w", encoding="utf-8")
        
    out_f = open_new_chunk(chunk_index)
    
    with open(input_file, "rb") as f:
        with dctx.stream_reader(f) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8', errors='ignore')
            
            for line in text_stream:
                # Check for new game boundary
                if line.startswith("[Event ") and current_size >= max_chunk_size_bytes:
                    out_f.close()
                    chunk_index += 1
                    out_f = open_new_chunk(chunk_index)
                    current_size = 0
                
                # Write line and update tracking size
                # encoded length approximates byte size written
                out_f.write(line)
                current_size += len(line.encode('utf-8'))

    if out_f and not out_f.closed:
        out_f.close()
        
    end_time = time.time()
    print(f"\nCompleted splitting into {chunk_index} files!")
    print(f"Time taken: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    input_path = os.path.join("datasets", "lichess_sample.pgn.zst")
    output_path = os.path.join("datasets", "chunks")
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Please ensure the dataset exists.")
    else:
        split_pgn(input_path, output_path)
