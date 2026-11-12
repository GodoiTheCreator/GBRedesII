def bpsk(data):
    final_data = []
    for bit in data:
        if bit == 1:
            final_data.append(1)
        else:
            final_data.append(-1)
    return final_data

def qpsk(data):
    final_data = []
    for i in range(0, len(data), 2):
        if data[i] == 0 and data[i + 1] == 0:
            final_data.append((1, 1))
        elif data[i] == 0 and data[i + 1] == 1:
            final_data.append((-1, 1))
        elif data[i] == 1 and data[i + 1] == 0:
            final_data.append((1, -1))
        else:
            final_data.append((-1, -1))
    return final_data

def sixteen_qam(data):
    final_data = []
    for i in range(0, len(data), 4):
        # Simplified 16-QAM mapping (in practice, this would be more complex)
        if data[i] == 0 and data[i + 1] == 0 and data[i + 2] == 0 and data[i + 3] == 0:
            final_data.append((1, 1))
        elif data[i] == 0 and data[i + 1] == 0 and data[i + 2] == 0 and data[i + 3] == 1:
            final_data.append((-1, 1))
        elif data[i] == 0 and data[i + 1] == 0 and data[i + 2] == 1 and data[i + 3] == 0:
            final_data.append((1, -1))
        else:
            final_data.append((-1, -1))
    return final_data