import fooddatacentral as fdc
import pandas as pd
from eep153_tools.sheets import read_sheets
import numpy as np

def nutrition(age, sex, activity_level = False):
    # possible additional args pregnant, activity_level
    """
    takes the following
    age: integer from 2 through 120
    sex: either "F" for female or "M" for male
    activity_level: "Sedentary", "Moderately
Active", or "Active".
    outputs:
    A series object indexed by nutrition category with the series being the values respective 
    to the age range from input. Energy is changed based on activity level or baseline activity which is sedentary I believe.
    """
    if age<2 or age > 120:
        return "not valid age"
    RDIs = read_sheets('https://docs.google.com/spreadsheets/d/1xqixhrAoDq9rWJf_FC3Y2eXdd010DTLPCS7JJMCfwP8/edit?usp=sharing', sheet="rda")
    RDIs = RDIs.set_index('Nutrient')
    if sex == 'F':
        fullsex = 'Female'
    else: fullsex = 'Male'
    if activity_level:
        active_energy = activity(age, sex, activity_level)
    if age<4:
        if activity_level:
            output = RDIs['Child_1_3']
            output[0] = active_energy
            return output
        return RDIs['C 1-3']
    else:
        agerange = find_age_range(age)
        if activity_level:
            output = RDIs[f'{fullsex}_{agerange}']
            output[0] = active_energy
            return output
        return RDIs[f'{fullsex}_{agerange}']


def activity(age, sex, activity_level):
    activities = read_sheets('https://docs.google.com/spreadsheets/d/1xqixhrAoDq9rWJf_FC3Y2eXdd010DTLPCS7JJMCfwP8/edit?usp=sharing', sheet="activity_levels")
    activities = activities.set_index('Age')
    if age>18:
        activedic = {
        '19-20': np.arange(19,21),
        '21-25': np.arange(21,26),
        '26-30': np.arange(26,31),
        '31-35': np.arange(31,36),
        '36-40': np.arange(36,41),
        '41-45': np.arange(41,46),
        '46-50': np.arange(46,51),
        '51-55': np.arange(51,56),
        '56-60': np.arange(56,61),
        '61-65': np.arange(61,66),
        '66-70': np.arange(66,71),
        '71-75': np.arange(71,76),
        '76 and up': np.arange(76,120)
        }
        ager = "None"
        for age_range, ages in activedic.items():
            if age in ages:
                ager = age_range
        return activities.loc[ager, f"{sex} - {activity_level}"]
    else:
        return activities.loc[ager, f"{sex} - {activity_level}"]


def find_age_range(age):
    agedict = {'1_3': np.arange(1,4),
          '4_8': np.arange(4,9),
          '9_13': np.arange(9,14),
          '14_18': np.arange(14,19),
          '19_30': np.arange(19,31),
          '31_50': np.arange(31,51),
          '51U': np.arange(51,120)}
    for age_range, ages in agedict.items():
        if age in ages:
            return age_range
    return "Age not in range"