import os

output_dir = "output/Technology"
if os.path.exists(output_dir):
    print(f"Listing {output_dir}:")
    for name in os.listdir(output_dir):
        print(f"'{name}' - Len: {len(name)}")
        # Print repr to see escapes
        print(f"Repr: {repr(name)}")
else:
    print(f"{output_dir} does not exist")
