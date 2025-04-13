import json
import math
import requests
import os
import time
from bs4 import BeautifulSoup


#TODO: incorporate earnings days (disclude), acount for bid/ask differential as a percentage of the total stock price




def open_json_for_date(sym1, sym2, interval, month):
    link1 = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+sym1+"&interval="+interval+"&month="+month+"&outputsize=full&extended_hours=false&apikey=NJC0H9L2L2CS64SU"
    link2 = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+sym2+"&interval="+interval+"&month="+month+"&outputsize=full&extended_hours=false&apikey=NJC0H9L2L2CS64SU"


    #getting the exact text from these links and writing them to their respective JSON files
    response1 = requests.get(link1)
    content1 = response1.content
    soup1 = BeautifulSoup(content1, "html.parser")
    text1 = soup1.get_text()
    sym1_file = open("ticker1.json", "w")
    sym1_file.write(text1)


    response2 = requests.get(link2)
    content2 = response2.content
    soup2 = BeautifulSoup(content2, "html.parser")
    text2 = soup2.get_text()
    sym2_file = open("ticker2.json", "w")
    sym2_file.write(text2)


    sym1_file.close()
    sym2_file.close()
    one = open("ticker1.json")
    two = open("ticker2.json")
    #opening the JSON
    tick1 = json.load(one)
    tick2 = json.load(two)
    return tick1, tick2


def prev_month(month):
    year = int(month[:4])
    month = int(month[5])*10 + int(month[6])
    if(month > 1):
        month -= 1
    else:
        month = 12
        year-=1
    month_str = ""
    if(month < 10):
        month_str = "0" + str(month)
    else:
        month_str = str(month)
    return str(year) + "-" + month_str


def num_data_points(interval, tick1, tick2):
    data_points = 0


    for date in tick1["Time Series (" + interval + ")"]:
        close1 = float(tick1["Time Series (" + interval + ")"][date]["4. close"])
        close2 = 0.0
        try:
            close2 = float(tick2["Time Series (" + interval + ")"][date]["4. close"]) #sometimes data points are missing, so this error must be checked
        except:
            continue
        data_points += 1


    return data_points


def ave_value_helper(interval, tick1):
    sum_value = 0
    num_data_points = 0
    for date in tick1["Time Series (" + interval + ")"]:
        close1 = float(tick1["Time Series (" + interval + ")"][date]["4. close"])
        sum_value += close1
        num_data_points += 1


    return sum_value, num_data_points


def stdev_sum(ratio, interval, tick1, tick2):
   
    stdev_sum = 0


    for date in tick1["Time Series (" + interval + ")"]:
        close1 = float(tick1["Time Series (" + interval + ")"][date]["4. close"])
        close2 = 0.0
        try:
            close2 = float(tick2["Time Series (" + interval + ")"][date]["4. close"]) #sometimes data points are missing, so this error must be checked
        except:
            continue
        close2 *= ratio
        stdev_sum += abs(close2-close1)


    return stdev_sum


#def stationarity - find stdev of stats in different time spans


#this will return the multiple sums needed for calculating r, these will be further summed in looper, then outside of looper r will be calculated
def r_val_sums(interval, tick1, tick2):
    ave1info = ave_value_helper(interval, tick1)
    ave2info = ave_value_helper(interval, tick2)
    ave1 = ave1info[0]/ave1info[1]
    ave2 = ave2info[0]/ave2info[1]
    #(xi - xave)(yi - yave) = numerator_val
    #(xi-xave)^2 = square1
    #(yi-yave)^2 = square2
    numerator_val = 0
    square1 = 0
    square2 = 0
    for date in tick1["Time Series (" + interval + ")"]:
        close1 = float(tick1["Time Series (" + interval + ")"][date]["4. close"])
        close2 = 0.0
        try:
            close2 = float(tick2["Time Series (" + interval + ")"][date]["4. close"]) #sometimes data points are missing, so this error must be checked
        except:
            continue
        x_minus_ave = close1 - ave1
        y_minus_ave = close2 - ave2
        numerator_val += x_minus_ave * y_minus_ave
        square1 += math.pow(x_minus_ave, 2)
        square2 += math.pow(y_minus_ave, 2)
    return numerator_val, square1, square2


def looper(sym1, sym2, interval, month, look_back):
    data_points = 0
    data_points_ave_value1 = 0 #specific to the average value function, as this does not check if the second ticker does not have a data point, so it ends up having more data points
    val1_sum = 0
    data_points_ave_value2 = 0
    val2_sum = 0
    dev_sum = 0


    #for r
    numerator_val = 0
    square1 = 0
    square2 = 0


    #summing all of the values then dividing by corresponding data points
    for i in range(look_back):
        ticks = open_json_for_date(sym1, sym2, interval, month)
        tick1 = ticks[0]
        tick2 = ticks[1]


        val_info = ave_value_helper(interval, tick1)
        data_points_ave_value1 += val_info[1]
        val1_sum += val_info[0]
        current_ave1 = val1_sum/data_points_ave_value1


        val2_info = ave_value_helper(interval, tick2)
        data_points_ave_value2 += val2_info[1]
        val2_sum += val2_info[0]
        current_ave2 = val2_sum/data_points_ave_value2


        #referring to datapoints for stdev
        data_points_current = num_data_points(interval, tick1, tick2)
        ratio = current_ave1/current_ave2
        #finding the ratio of a given month to get stdev for that month
        data_points += data_points_current
        dev_sum += stdev_sum(ratio, interval, tick1, tick2)


        #for r
        r_info = r_val_sums(interval, tick1, tick2)
        numerator_val += r_info[0]
        square1 += r_info[1]
        square2 += r_info[2]


        month = prev_month(month)
   
    final_val1 = val1_sum/data_points_ave_value1
    final_val2 = val2_sum/data_points_ave_value2
    final_stdev = dev_sum/data_points


    #calculating r
    final_r = numerator_val/(math.sqrt(square1*square2))


    return final_val1, final_val2, final_stdev, final_r




def create_files_for_backtest(sym1, sym2, interval, month, look_back, look_back2):
    days_in_month = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
    for i in range(look_back):
        link1 = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+sym1+"&interval="+interval+"&month="+month+"&outputsize=full&extended_hours=false&apikey=NJC0H9L2L2CS64SU"
        link2 = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+sym2+"&interval="+interval+"&month="+month+"&outputsize=full&extended_hours=false&apikey=NJC0H9L2L2CS64SU"
        file_name_1 = str(i) + "_1.json"
        file_name_2 = str(i) + "_2.json"
        #getting the exact text from these links and writing them to their respective JSON files
        response1 = requests.get(link1)
        content1 = response1.content
        soup1 = BeautifulSoup(content1, "html.parser")
        text1 = soup1.get_text()
        sym1_file = open(file_name_1, "w")
        sym1_file.write(text1)
        sym1_file.close()
        open(file_name_1)


        response2 = requests.get(link2)
        content2 = response2.content
        soup2 = BeautifulSoup(content2, "html.parser")
        text2 = soup2.get_text()
        sym2_file = open(file_name_2, "w")
        sym2_file.write(text2)
        sym2_file.close()
        open(file_name_2)


        if i%13 == 0 and i != 0:
            print("Minute delay due to api limit")
            time.sleep(60)


        month = prev_month(month)
    #now, calculate how many extra months need to be added
    extra_months = 0
    month_itr = int(month[5])*10 + int(month[6]) - 1 #-1 because we will iterate through the list
    while look_back2 > 0:
        extra_months += 1
        look_back2 -= days_in_month[month_itr]
        month_itr -= 1
        if month_itr == 0:
            month_itr = 11
   
    for i in range(extra_months):
        if (look_back + i) % 14 == 0 and (look_back+i) != 0:
            print("Minute delay due to api limit")
            time.sleep(60)
        link1 = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+sym1+"&interval="+interval+"&month="+month+"&outputsize=full&extended_hours=false&apikey=NJC0H9L2L2CS64SU"
        link2 = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+sym2+"&interval="+interval+"&month="+month+"&outputsize=full&extended_hours=false&apikey=NJC0H9L2L2CS64SU"
        file_name_1 = str(look_back + i) + "_1.json"
        file_name_2 = str(look_back + i) + "_2.json"
        #getting the exact text from these links and writing them to their respective JSON files
        response1 = requests.get(link1)
        content1 = response1.content
        soup1 = BeautifulSoup(content1, "html.parser")
        text1 = soup1.get_text()
        sym1_file = open(file_name_1, "w")
        sym1_file.write(text1)
        sym1_file.close()
        open(file_name_1)


        response2 = requests.get(link2)
        content2 = response2.content
        soup2 = BeautifulSoup(content2, "html.parser")
        text2 = soup2.get_text()
        sym2_file = open(file_name_2, "w")
        sym2_file.write(text2)
        sym2_file.close()
        open(file_name_2)


        month = prev_month(month)


def find_num_months(month, look_back, look_back2):
    days_in_month = [20,20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
    months = look_back
    for i in range(look_back):
        month = prev_month(month)


    month_itr = int(month[5])*10 + int(month[6])-1 #because we will iterate through the list
    while look_back2 > 0:
        months += 1
        look_back2 -= days_in_month[month_itr]
        month_itr -= 1
        if month_itr == 0:
            month_itr = 11
   
    return months
   
def delete_files_for_backtest(month, look_back, look_back2):
    num_months = find_num_months(month, look_back, look_back2)
    for i in range(num_months):
        file_name1 = str(i) + "_1.json"
        file_name2 = str(i) + "_2.json"
        os.remove(file_name1)
        os.remove(file_name2)


#getting data for each day


def get_ave_val_1day(interval, current_date, tick):
    data_points = 0
    sum_val = 0
    start_day_int = int(current_date[8])*10 + int(current_date[9])
    for date in tick["Time Series (" + interval + ")"]:
        close1 = float(tick["Time Series (" + interval + ")"][date]["4. close"])
        day_int = int(date[8])*10 + int(date[9])
        if day_int < start_day_int:
            break
        if (date[:10] == current_date[:10]):
            sum_val += close1
            data_points += 1
    return sum_val, data_points


def get_stdev_1day(ratio, interval, current_date, tick1, tick2):
    data_points = 0
    sum_stdev = 0
    start_day_int = int(current_date[8])*10 + int(current_date[9])
    for date in tick1["Time Series (" + interval + ")"]:
        close1 = float(tick1["Time Series (" + interval + ")"][date]["4. close"])
        try:
            close2 = float(tick2["Time Series (" + interval + ")"][date]["4. close"])
        except:
            continue
        day_int = int(date[8])*10 + int(date[9])
        if day_int < start_day_int:
            break
        if (date[:10] == current_date[:10]):
            sum_stdev += abs(close1 - ratio*close2)
            data_points += 1
    return sum_stdev, data_points


def go_back_to_day(day, look_back2, ticks, interval, currenti):
    #day = date[:10]
    found_init_day = False
    day_count = 0
    i = 0
    last_day = ""
    should_break = False
    while day_count < look_back2:
        for date in ticks[i + currenti]["Time Series (" + interval + ")"]:
            if date[:10] == day:
                found_init_day = True
                continue
            if found_init_day:
                if last_day != date[:10]:
                    last_day = date[:10]
                    day_count += 1
                    if day_count == look_back2:
                        should_break = True
                        break
        if should_break:
            break
        i += 1
    return last_day, i




def get_data_window_lists(ticks1, ticks2, interval, look_back, look_back2):
    window_list_ave1 = []
    window_list_ave2 = []
    window_list_stdev = []
    window_ave1_sum = 0
    window_ave1_sum_num_data = 0
    window_ave2_sum = 0
    window_ave2_sum_num_data = 0
    window_ratio = 0
    window_stdev = 0
    window_stdev_num_data = 0


    #getting the initial window
    #checking what the first day is then discluding it, as including it would create look-ahead bias


    start_date = ""
    last_day = ""
    day_count = 0
    i = 0
    start = True
    while day_count < look_back2:
        for date in ticks1[i]["Time Series (" + interval + ")"]:
            close1 = float(ticks1[i]["Time Series (" + interval + ")"][date]["4. close"])
            if start:
                start_date = date[:10]
                start = False
            if date[:10] == start_date:
                continue
            if date[:10] != last_day:
                day_count += 1
            window_ave1_sum += close1
            window_ave1_sum_num_data += 1
            last_day = date[:10]
        i += 1
    start_date = ""
    last_day = ""
    day_count = 0
    i = 0
    start = True
    while day_count < look_back2:
        for date in ticks2[i]["Time Series (" + interval + ")"]:
            close2 = float(ticks2[i]["Time Series (" + interval + ")"][date]["4. close"])
            if start:
                start_date = date[:10]
                start = False
            if date[:10] == start_date:
                continue
            if date[:10] != last_day:
                day_count += 1
            window_ave2_sum += close2
            window_ave2_sum_num_data += 1
            last_day = date[:10]
        i += 1
    start_date = ""
    last_day = ""
    day_count = 0
    i = 0
    ratio = (window_ave1_sum/window_ave1_sum_num_data)/(window_ave2_sum/window_ave2_sum_num_data)
    start = True
    while day_count < look_back2:
        for date in ticks1[i]["Time Series (" + interval + ")"]:
            close1 = float(ticks1[i]["Time Series (" + interval + ")"][date]["4. close"])
            try:
                close2 = float(ticks2[i]["Time Series (" + interval + ")"][date]["4. close"])
            except:
                continue
            if start:
                start_date = date[:10]
                start = False
            if date[:10] == start_date:
                continue
            if date[:10] != last_day:
                day_count += 1
            close2 *= ratio
            window_stdev += abs(close2-close1)
            window_stdev_num_data += 1
            last_day = date[:10]
        i += 1
    window_list_ave1.append((window_ave1_sum, window_ave1_sum_num_data))
    window_list_ave2.append((window_ave2_sum, window_ave2_sum_num_data))
    window_list_stdev.append((window_stdev, window_stdev_num_data))
   
    #making a new window for each day
    #MAKE THESE FUNCTIONS
    #subtract current day's data, go to the end of look_back2, add this days data - do this for the aves and stdev
    last_day = ""
    start_date = ""
    skip_day = True
    day_count = 0#make a window_list for each one
    new_sum = 0
    new_data_points = 0
    for i in range(look_back):
        for date in ticks1[i]["Time Series (" + interval + ")"]:
            day = date[:10]
            if skip_day:
                start_date = day
                skip_day = False
            if start_date == day:
                continue
            if day != last_day:
                get_ave_val = get_ave_val_1day(interval, date, ticks1[i])
                day_ave_sum = get_ave_val[0]
                num_data = get_ave_val[1] #WHENEVER YOU SEE A FUNCTION BEING USED TWICE LIKE THIS, CALL IT ONCE IN A VARIABLE THEN USE THAT VARIABLE
                new_sum = window_list_ave1[-1][0] - day_ave_sum
                new_data_points = window_list_ave1[-1][1] - num_data
               
                back_day_info = go_back_to_day(day, look_back2, ticks1, interval, i)
                new_month = back_day_info[1]
                new_day = back_day_info[0]
                new_tick = ticks1[i + new_month]
                get_ave_val = get_ave_val_1day(interval, new_day, new_tick)
                new_sum += get_ave_val[0]
                new_data_points += get_ave_val[1]


                window_list_ave1.append((new_sum, new_data_points))
                day_count += 1
                last_day = day


#============
    last_day = ""
    start_date = ""
    skip_day = True
    day_count = 0#make a window_list for each one
    new_sum = 0
    new_data_points = 0
    for i in range(look_back):
        for date in ticks2[i]["Time Series (" + interval + ")"]:
            day = date[:10]
            if skip_day:
                start_date = day
                skip_day = False
            if start_date == day:
                continue
            if day != last_day:
                get_ave_val = get_ave_val_1day(interval, date, ticks2[i])
                day_ave_sum = get_ave_val[0]
                num_data = get_ave_val[1] #WHENEVER YOU SEE A FUNCTION BEING USED TWICE LIKE THIS, CALL IT ONCE IN A VARIABLE THEN USE THAT VARIABLE
                new_sum = window_list_ave2[-1][0] - day_ave_sum
                new_data_points = window_list_ave2[-1][1] - num_data
               
                back_day_info = go_back_to_day(day, look_back2, ticks1, interval, i)
                new_month = back_day_info[1]
                new_day = back_day_info[0]
                new_tick = ticks2[i + new_month]
                get_ave_val = get_ave_val_1day(interval, new_day, new_tick)
                new_sum += get_ave_val[0]
                new_data_points += get_ave_val[1]


                window_list_ave2.append((new_sum, new_data_points))
                day_count += 1
                last_day = day


#===========
    #stdev goes here
    last_day = ""
    new_day = ""
    new_month = 0
    start_date = ""
    skip_day = True
    day_count = 0
    for i in range(look_back):
        for date in ticks1[i]["Time Series (" + interval + ")"]:
            day = date[:10]
            if skip_day:
                start_date = day
                skip_day = False
            if start_date == day:
                continue
            if day != last_day:
                window_ave1 = window_list_ave1[day_count]
                window_ave2 = window_list_ave2[day_count]
                ratio1 = (window_ave1[0]/window_ave1[1])/(window_ave2[0]/window_ave2[1])


                get_stdev = get_stdev_1day(ratio1, interval, date, ticks1[i], ticks2[i])
                day_ave_sum = get_stdev[0]
                num_data = get_stdev[1] #WHENEVER YOU SEE A FUNCTION BEING USED TWICE LIKE THIS, CALL IT ONCE IN A VARIABLE THEN USE THAT VARIABLE
                new_sum = window_list_stdev[-1][0] - day_ave_sum
                new_data_points = window_list_stdev[-1][1] - num_data
               
                back_day_info = go_back_to_day(day, look_back2, ticks1, interval, i)
                new_month = back_day_info[1]
                new_day = back_day_info[0]
                new_tick1 = ticks1[i + new_month]
                new_tick2 = ticks2[i + new_month]
                get_stdev = get_stdev_1day(ratio1, interval, new_day, new_tick1, new_tick2)
                new_sum += get_stdev[0]
                new_data_points += get_stdev[1]


                window_list_stdev.append((new_sum, new_data_points))
                day_count += 1
                last_day = day


    return (window_list_ave1, window_list_ave2, window_list_stdev)
#for the first "data window" - will be added to and subtracted to


#for the backtest
#will iterate through all of the necessary data points by being looped through look_back and look_back2 and starting at the correct day
def next_interval(time, interval, ticks1, ticks2, monthsITR):


    year = int(time[:4])
    month = 10*int(time[5]) + int(time[6])
    day = 10*int(time[8]) + int(time[9])
    hour = 10*int(time[11]) + int(time[12])
    minute = 10*int(time[14]) + int(time[15])
   
    #find when the last day of the month is to know when to go to the next month
    #MONTHS ITR WILL NEED TO START AT THE HIGHEST MONTH BECAUSE THE ORDER IS BACKWARDS and then be subtracted from
    last_day = 0
    for date in ticks1[monthsITR]["Time Series (" + interval + ")"]:
        last_day = 10*int(date[8]) + int(date[9])
        break


    minute += int(interval[:-3]) #so if it were 5min, this would become 5 because m is the -3 indice?
    if (minute == 60):
        minute = 0
        hour += 1
    if hour == 16:
        if interval == "60min":
            hour = 10
        else:
            hour = 9
            minute = 30
        day += 1
    if (day > last_day): #remember, you need to deal with weekends
        minute = 0
        if interval == "60min":
            hour = 10
        else:
            hour = 9
            minute = 30
        day = 1
        monthsITR -= 1 #starts at "last" month
        if (month == 12):
            month = 1
            year += 1
        else:
            month += 1
    day_string = ""
    hour_string = ""
    minute_string = ""
    month_string = ""
    if month < 10:
        month_string += "0"
    if day < 10:
        day_string += "0"
    if hour < 10:
        hour_string += "0"
    if minute < 10:
        minute_string += "0"
    month_string += str(month)
    day_string += str(day)
    hour_string += str(hour)
    minute_string += str(minute)
   
    new_date = str(year) + "-" + month_string + "-" + day_string + " " + hour_string + ":" + minute_string + ":00"


    try:
        close1 = float(ticks1[monthsITR]["Time Series (" + interval + ")"][new_date]["4. close"])
        close2 = float(ticks2[monthsITR]["Time Series (" + interval + ")"][new_date]["4. close"])
    except KeyError:
        close1 = -1
        close2 = -1 #if the data point doesn't exist for either
    return close1, close2, new_date, monthsITR


   


#when going back through the months in look_back2, make sure to add/subtract from the current sums rather than looping through the data all over again for efficiency
def backtest(sym1, sym2, interval, month, z_score, stop_loss , balance, look_back, look_back2):
    # "sell" when it crosses the ratio again, whatever that may now be, or when the stop-loss is hit
    create_files_for_backtest(sym1, sym2, interval, month, look_back, look_back2)


    month_count = find_num_months(month, look_back, look_back2)
    ticks1 = []
    ticks2 = []
    for i in range(month_count):
        file_1 = open(str(i) + "_1.json")
        file_2 = open(str(i) + "_2.json")
        t1 = json.load(file_1)
        t2 = json.load(file_2)
        ticks1.append(t1)
        ticks2.append(t2)
        file_1.close()
        file_2.close()


    #window list appears to be working !!!
    window_list = get_data_window_lists(ticks1, ticks2, interval, look_back, look_back2)
    #remember, you need to deal with the fact that the list starts at the most recent date (AKA the end date of the backtest)


    window_list_ave1 = window_list[0]
    window_list_ave2 = window_list[1]
    window_list_stdev = window_list[2]
   
    #close1, close2, new_date, monthsITR
    #print(next_interval(start, interval, ticks1, ticks2, start_month))


    delete_files_for_backtest(month, look_back, look_back2)


    #gettng the last data point
    last_time = ""
    for date in ticks1[0]["Time Series (" + interval + ")"]:
        try:
            ticks2[0]["Time Series (" + interval + ")"][date]["4. close"]
        except:
            continue
        last_time = date
        break
   
    start = month
    for i in range(look_back-1):
        start = prev_month(start)
    if interval == "60min":
        start += "-01 10:00:00"
    else:
        start += "-01 09:30:00"
    #now iterate through each point using the function next_interval (-1 if no data point) and run the backtest - remember to account for the first value before doing interval
    holding = False
    AoverB = False #when a position is taken and A > B*ratio
    long = 0
    short = 0 #these are the values at which a position is taken
    day_when_trade_taken = 0
   
    time = start
    day_trades = [0] #to prevent pdt, day trades counted for each day
    last_day = time[:10]
    month_itr = look_back-1 #not the actual month, just which file we are using
    #count days to accurately go through windows lists (don't count if -1) - starts at len(window_list) because there is one day for each window - will be decremented from
    day_count = len(window_list_ave1)
    first_invalid = False
    try:
        close2 = float(ticks2[month_itr]["Time Series (" + interval + ")"][time]["4. close"])
        close1 = float(ticks1[month_itr]["Time Series (" + interval + ")"][time]["4. close"])
        #TRADING RULES NEED TO BE ADDED HERE TO ALLOW IT TO PLACE A TRADE ON THE FIRST INTERVAL
    except:
        first_invalid = True
    while time != last_time:


        next = next_interval(time, interval, ticks1, ticks2, month_itr)
        month_itr = next[3]
        time = next[2]
        close1 = next[0]
        close2 = next[1]


        if (time[:10] != last_day and close1 != -1):#-1 if not business day
            if not first_invalid:
                day_count -= 1
            else:
                first_invalid = False #shouldn't decrement if the first group of days are invalid (think about it)
            last_day = time[:10] #WHEN USING TO GO THROUGH WINDOW LIST, DO DAY_COUNT - 1
            day_trades.append(0)
       
        ave1_info = window_list_ave1[day_count-1]
        ave2_info = window_list_ave2[day_count-1]
        stdev_info = window_list_stdev[day_count-1]
        ave1 = ave1_info[0]/ave1_info[1]
        ave2 = ave2_info[0]/ave2_info[1]
        stdev = stdev_info[0]/stdev_info[1]
        ratio = ave1/ave2


        #pdt counter
        pdt = False
        for i in range(min(5, len(day_trades))):
            pdt = day_trades[-i-1]
            if pdt:
                break
       
        #TRADING RULES START HERE------------------
        if not pdt:
            if (close1 > close2*ratio and not holding and abs(close1-close2*ratio) >= z_score*stdev and close1 != -1):
                print("buy", time, balance)
                holding = True
                AoverB = True
                long = close2
                short = close1
                day_when_trade_taken = day_count
            if (close1 < close2*ratio and not holding and abs(close1-close2*ratio) >= z_score*stdev and close1 != -1):
                print("buy", time, balance)
                holding = True
                AoverB = False
                long = close1
                short = close2
                day_when_trade_taken = day_count
            if (AoverB and holding and close1 < close2*ratio and close1 != -1 and not pdt):
                holding = False
                balance = (1 + (short-close1)/short)*balance/2 + (1 + (close2-long)/long)*balance/2
                print("sell", time, balance)
                if day_count == day_when_trade_taken:
                    day_trades[-1] = True
            if (not AoverB and holding and close1 > close2*ratio and close1 != -1 and not pdt):
                holding = False
                balance = (1 + (short-close2)/short)*balance/2 + (1 + (close1-long)/long)*balance/2
                print("sell", time, balance)
                if day_count == day_when_trade_taken:
                    day_trades[-1] = True
            #stop loss below
            if (AoverB and holding and close1 != -1 and not pdt):
                unrealized = (1 + (short-close1)/short)*balance/2 + (1 + (close2-long)/long)*balance/2
                if 1+((unrealized - balance)/balance) <= (1-stop_loss/100):
                    print(unrealized, balance, 1-stop_loss/100)
                    balance = unrealized
                    holding = False
                    print("sell at stop-loss", time, balance)
                    if day_count == day_when_trade_taken:
                        day_trades[-1] = True
            if (not AoverB and holding and close1 != -1 and not pdt):
                unrealized = (1 + (short-close2)/short)*balance/2 + (1 + (close1-long)/long)*balance/2
                if 1+((unrealized - balance)/balance) <= (1-stop_loss/100):
                    print(unrealized, balance, 1-stop_loss/100)
                    balance = unrealized
                    holding = False
                    print("sell at stop-loss", time, balance)
                    if day_count == day_when_trade_taken:
                        day_trades[-1] = True
   
    return balance


       


if __name__ == "__main__":
    #TODO: have something that allows you to change parameters and re run the backtest before deleting the files
   
    print("Analyzing and backtesting stock/ETF pairs")
    print()
    sym1 = input("Enter ticker 1: ").upper()
    sym2 = input("Enter ticker 2: ").upper()
    month = input("Enter month (YYYY-MM): ")
    look_back = int(input("Enter # months to base stats on: ")) #if this were 3, for each date we would do the stdev, regression calculation based on the past 3 months
    interval = input("Enter interval (1min, 5min, 15min, 30min, 60min): ")
    backtestYN = input("Backtest this pair? (Y/N): ").upper()
    values = looper(sym1, sym2, interval, month, look_back)
    ave_val_sym1 = values[0]
    ave_val_sym2 = values[1]
    ratio = ave_val_sym1/ave_val_sym2
    stdev = values[2]
    r = values[3]
    print()
    print("==========================")
    print()
    print(("Average value of " + sym1 + ":"), round(ave_val_sym1,2))
    print(("Average value of " + sym2 + ":"), round(ave_val_sym2,2))
    print(("Average ratio (" + sym1 + "/" + sym2 + "):"), round(ratio,4))
    print("Standard deviation as a percentage of average value:", round(100*stdev/ave_val_sym1,2), "%")
    print("R:", round(r,4))
    print()
    if (backtestYN == "Y"):
        print("Starting backtest")
        print()
        look_back2 = int(input("Enter look-back for each data point (days): "))
        balance = float(input("Enter starting balance: "))
        z_score = float(input("Enter the target z-score: "))
        stop_loss = float(input("Enter the stop-loss (%): "))
        print(backtest(sym1, sym2, interval, month, z_score, stop_loss, balance, look_back, look_back2))
   
    #print(backtest("JPEQ", "SPY", "1min", "2020-01", 1, 5, 1000, 12, 10))
    '''
    print(backtest("PTEN", "HP", "1min", "2023-01", 1, 5, 1000, 12, 10))
    time.sleep(60)
    print(backtest("PTEN", "HP", "1min", "2022-01", 1, 5, 1000, 12, 10))
    time.sleep(60)
    print(backtest("PTEN", "HP", "1min", "2021-01", 1, 5, 1000, 12, 10))
    time.sleep(60)
    print(backtest("PTEN", "HP", "1min", "2020-01", 1, 5, 1000, 12, 10))
    '''

