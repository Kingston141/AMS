# generate_encryption_keys.py

import json
import hashlib

# Use raw string to handle Windows path spaces
INPUT_FILE = r"C:\Users\kings\Desktop\AMS\Encodings and Embeddings\encryption\known_faces_encodings.json"
OUTPUT_FILE = r"C:\Users\kings\Desktop\AMS\Encodings and Embeddings\encryption\face_encryption_db.json"

def generate_key_from_encoding(encoding):
    rounded = [round(e, 5) for e in encoding]
    enc_str = json.dumps(rounded)
    return hashlib.sha256(enc_str.encode()).hexdigest()[:16]

def generate_encryption_db():
    with open(INPUT_FILE, 'r') as f:
        face_data = json.load(f)

    encryption_db = []
    keys_set = set()

    for person in face_data:
        key = generate_key_from_encoding(person["encoding"])
        if key not in keys_set:
            encryption_db.append({
                "encryption_key": key,
                "name": person["name"]
            })
            keys_set.add(key)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(encryption_db, f, indent=4)
    print(f"✅ Saved to: {OUTPUT_FILE} with {len(encryption_db)} unique keys.")

if __name__ == "__main__":
    generate_encryption_db()
