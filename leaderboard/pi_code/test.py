import pickle

data = pickle.load(open("input_data.pkl", "rb"))

print(data.keys())
print(data['IMU'])
print(data['GPS'])
print(data['LIDAR'])
print(data['Speed'])
print(data['Center'])

dat = pickle.load(open("n015-2018-07-24-11-22-45+0800.pkl", "rb"))
# print(dat)
