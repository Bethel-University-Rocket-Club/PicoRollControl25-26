def best_fit(X, Y):

    xbar = sum(X)/len(X)
    ybar = sum(Y)/len(Y)
    n = len(X) # or len(Y)

    numer = sum([xi*yi for xi,yi in zip(X, Y)]) - n * xbar * ybar
    denum = sum([xi**2 for xi in X]) - n * xbar**2

    b = numer / denum
    a = ybar - b * xbar

    print('best fit line:\ny = {:.8f} + {:.8f}x'.format(a, b))

#speed -> [sample count, summed delta roll]
organized_data = {}

result_data = []

with open("data.csv", "r") as f:
    f.readline() #ignore the header line
    for line in f:
        #speed, time from speed start (ms), roll
        speed, time_from_start, delta_roll = [float(x) for x in line.split(",")]
        if speed in organized_data:
            organized_data[speed][0] += 1
            organized_data[speed][1] += delta_roll
        else:
            organized_data[speed] = [1, delta_roll]
            
speeds = list(organized_data)
for i in range(len(speeds)-1):
    cur_speed = speeds[i]
    next_speed = speeds[i+1]
    avg_speed_effect_high = abs(organized_data[cur_speed][1] / organized_data[cur_speed][0])
    avg_speed_effect_low = abs(organized_data[next_speed][1] / organized_data[next_speed][0])
    avg_speed_effect = (avg_speed_effect_high + avg_speed_effect_low) / 2
    avg_speed = (cur_speed + next_speed) / 2
    result_data.append([avg_speed, avg_speed_effect])
    
for data in result_data:
    print(data[0], data[1])
    
result_data.append([0, 0])
best_fit([x[1] for x in result_data], [x[0] for x in result_data])