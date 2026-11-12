def manchester(binary_message):
    final_data = []
    for bit in binary_message:
        if bit == 1:
            final_data.append(1)
            final_data.append(-1)
        else:
            final_data.append(-1)
            final_data.append(1)
    return final_data

def ami(binary_message):
    final_data = []
    for bit in binary_message:
        if bit == 1:
            final_data.append(1)
            final_data.append(-1)
        else:
            final_data.append(0)
            final_data.append(0)
    return final_data