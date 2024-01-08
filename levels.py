def read_level_bin(data):
    magic1 = data[0]
    data = data[1:]
    assert magic1 == 1

    obj_names_len = int.from_bytes(data[:4], byteorder="little")

    data = data[4:]
    obj_name_data = data[:obj_names_len]
    data = data[obj_names_len:]

    magic0 = int.from_bytes(data[:4], byteorder="little")
    data = data[4:]
    # assert magic0 == 0
    if magic0 != 0:
        print("Warning: Skipped a nested level file")
        return {}

    scripts_len = int.from_bytes(data[:4], byteorder="little")
    data = data[4:]

    scripts = {}
    for _ in range(scripts_len):
        script_name_offset = int.from_bytes(data[:4], byteorder="little")
        script_sz = int.from_bytes(data[4:8], byteorder="little")
        script = data[8 : 8 + script_sz]
        script_name = obj_name_data[script_name_offset:].split(b"\0", 1)[0].decode()
        scripts[script_name] = script
        data = data[8 + script_sz :]

    return scripts
