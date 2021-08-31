import pandas as pd
import zipfile
import tqdm
import os 


#creates accelerometer table
def get_timeseries(file):
    
    timeseries = pd.read_csv(file, names = ['time', 'x', 'y', 'z'])
    timeseries.time = pd.to_datetime(timeseries.time, unit='s')
    timeseries.time = pd.DatetimeIndex(timeseries.time).tz_localize('UTC').\
                                                    tz_convert('Europe/Moscow')
    timeseries.time = pd.DatetimeIndex(timeseries.time).tz_localize(None) 
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
def name_csv(file, time):
    name = file.loc[file.end == time].action.values[0]
    if '/' in name:
        name = name.replace('/', '|')
    return name

def make_folder(name):
    try:
        os.mkdir('{}_folder'.format(name))
        return True
    except FileExistsError:
        pass
  
def crop_timeseries(files_array):
    for pair in files_array:
        for begin, end in tqdm.tqdm(pair[0][['begin', 'end']].values):
            if end in pd.DatetimeIndex(pair[1].time).floor('S'):
                name = name_csv(pair[0], end)
                make_folder(pair[2])

                cropped = pair[1].loc[(pd.DatetimeIndex(pair[1].time).time >= begin)
                                   & (pd.DatetimeIndex(pair[1].time).time <= end)]
                cropped.to_csv('{}_folder/{}.csv'.format(pair[2], name), mode = 'a', header = False)              

def main():
    files = load_data('/home/rafael/Work/WatchActionRecognition/Data/Raw_data/test.zip')
    crop_timeseries(files)
    
if __name__ == "__main__":
    main()