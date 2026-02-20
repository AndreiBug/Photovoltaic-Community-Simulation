from datetime import datetime

def epoch_to_datetime(epoch_time):
    return datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    epoch = 890344800
    print("Epoch:", epoch)
    print("Data si ora:", epoch_to_datetime(epoch))
