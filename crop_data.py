import pandas as pd
import datetime
import zipfile
import tqdm
import os 


#creates accelerometer table
def get_timeseries(file):
    
    timeseries = pd.read_csv(file, names = ['date', 'x', 'y', 'z'])
    timeseries.date = pd.to_datetime(timeseries.date, unit='s')
    timeseries.date = [datetime.datetime.time(d) for d in timeseries.date] 

    return timeseries

#creates detalisation table
def get_detalisation(file):
    
    detalisation = pd.read_csv(file, names = ['action', 'begin', 'end'])
    detalisation[['begin', 'end']] = detalisation[['begin', 'end']].apply(pd.to_datetime)
    detalisation.begin = pd.DatetimeIndex(detalisation.begin).time
    detalisation.end = pd.DatetimeIndex(detalisation.end).time
    return detalisation

#data processing
def load_data(file_name):
    zfile = zipfile.ZipFile(file_name, 'r')
    files = [] 
    
    for file in tqdm.tqdm(zfile.namelist()):
        if 'actions' not in file:
            timeseries_name = os.path.splitext(file)[0] #directory name 
            file = zfile.open(file)
            timeseries_file = get_timeseries(file)

            file = zfile.open('{}_actions.csv'.format(timeseries_name))
            detalisation_file = get_detalisation(file)

            files.append([detalisation_file, timeseries_file, timeseries_name])
            
    zfile.close()

    return files

#creates file name
def folder_name_csv(file, time):
    name = file.loc[file.end == time].action.values[0]
    if '/' in name:
        name = name.replace('/', '|')
    return name

def file_name_csv(worker, action, actions):
    if worker in actions:
        actions[worker].append(action)
        count = actions[worker].count(action)
        name = '{}_{}_{}'.format(worker, action, count)
    else:
        actions[worker] = [action]
        name = '{}_{}_{}'.format(worker, action, 1)
    return name

def make_folder(name):
    try:
        os.mkdir('{}_folder'.format(name))
        return True
    except FileExistsError:
        pass

def make_timestamp(data):
    data['date'] = data['date'].apply(pd.Timestamp)
    data['date'] = data['date'].apply(pd.Timestamp.timestamp)

    return data
  
def crop_timeseries(files_array):
    for pair in files_array:
        action_dict = {}
        for begin, end in tqdm.tqdm(pair[0][['begin', 'end']].values):
            if end in pair[1].date.floor('S'):
                folder_name = folder_name_csv(pair[0], end)
                file_name = file_name_csv(pair[2], folder_name, action_dict)
                make_folder(pair[2])

                cropped = pair[1].loc[(pair[1].date.floor('S') >= begin)
                                   & (pair[1].date.floor('S') <= end)]
                cropped = make_timestamp(cropped)
                cropped.to_csv('{}_folder/{}.csv'.format(folder_name, file_name), mode = 'a', header = False)              

def main():
    files = load_data('/home/rafael/Work_copy/WatchActionRecognition/Data/Raw_data/actions.zip')
    crop_timeseries(files)
    
if __name__ == "__main__":
    main()