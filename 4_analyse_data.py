'''
This script retrieves the data extracted from script 3_extract_page_contents and calculates various related statistics.
Some outputs are saved into the dataframe as new columns. Some are printed out. Some are saved as graphs in the outputs folder.
'''
import numpy as np
import pandas as pd
import re
from matplotlib import pyplot as plt


df = pd.read_csv('dataset extract.csv',index_col=0)

'''
country_citizen is a mapping of the nationality of a person, to (a short form of) the country name.
It is used to check if a defendant's country matches the case's country.
Example:
{
    'Moroccan': 'morocc',
    'Ukrainian': 'ukrain'
}
'''
country_citizen = {}
with open('country_citizen.txt','r') as f:
    for row in f:
        citizen,country = row.strip().split(',')
        country_citizen[citizen] = country

# The following new columns are added to the dataframe
df.insert(1, column='defendant_country_match_case', value='-')
df.insert(1, column='victim_defendant_same_country', value='-')
df.insert(1, column='keyword_section_match_count', value='-')
df.insert(1, column='serious_crime', value='-')
df.insert(1, column='victims_type', value='-')
df.insert(1, column='num_criteria_met', value='-')
df.insert(1, column='meet_criteria', value='-')

# The following stats are calculated and print out to console
stats = {
    'imprisonment': {
        'no info': 0,
        'any has serious crime': 0,
        'all no serious crime': 0
    },
    'victims_type':{
        'all children': 0,
        'all adult': 0,
        'mix': 0,
        'unknown': 0,
        '-': 0
    },
    'victim_gender':{
        'male': 0,
        'female': 0,
        'child': 0,
        'unknown': 0
    },
    'victim_defendant_same_country':{
        'At least one match': 0,
        'Country not provided': 0,
        'Entire field unavailable': 0,
        'No match': 0
    },
    'defendant_country_match_case':{
        'At least one match': 0,
        'Defendant country unknown': 0,
        'Entire field unavailable': 0,
        'No match': 0
    }
}

# init counters
male_ages = []
female_ages = []
child_ages = []
unknown_ages = []
criteria_count = [0,0,0,0,0,0] # 6 criteria: acts, means, purpose, transnational, organised crime, serious crime (term of imprisonment >= 4 years)
case_total_criteria_met = [0,0,0,0,0,0,0] # from 0 criteria met to all 6 criteria met
all_defendants_countries = []

# for each row/case in dataframe
for i in range(len(df.index)):
    # check if all victims children -> can ignore means
    # also add to histogram of ages
    victims = df.loc[i, 'victims']
    if victims != '-':
        child = re.search('Child', victims, re.IGNORECASE)
        adult = re.search('Male', victims, re.IGNORECASE) or re.search('Female', victims, re.IGNORECASE)
        unknown = re.search('\? \?', victims, re.IGNORECASE)
        if child and not adult and not unknown: # confirmed only children present
            df.loc[i, 'victims_type'] = 'all children'
        elif child and adult: # confirmed a mix of children and adults
            df.loc[i, 'victims_type'] = 'mix'
        elif not child and adult and not unknown: # confirmed all adults present
            df.loc[i, 'victims_type'] = 'all adult'
        else: # in all other situations, no confirmation can be made
            df.loc[i, 'victims_type'] = 'unknown'

        # add to histogram of ages (currently in list form) depending on gender
        v = victims.split(' | ')
        for w in v:
            q = w.split('_')
            gender = q[0]
            age = q[1]
            if gender == '?':
                unknown_ages.append(int(age) if age.isnumeric() else -1)
            elif gender == 'Male':
                male_ages.append(int(age) if age.isnumeric() else -1)
            elif gender == 'Female':
                female_ages.append(int(age) if age.isnumeric() else -1)
            elif gender == 'Child':
                child_ages.append(int(age) if age.isnumeric() else -1)
            else:
                print('histogram of ages: gender not found')

    # check if any one victim is from the same country as any one defendant
    victims = df.loc[i, 'victims']
    defendants = df.loc[i, 'defendants']
    country_match_found = False
    unknown_country = False
    defendant_unknown_country = False
    defendant_country_match_case = False
    if victims != '-' and defendants != '-':
        vv = victims.split(' | ')
        dd = defendants.split(' | ')
        for v in vv: # for each victim
            v_countries = v.split('_')[2].split('-')
            for d in dd: # for each defendant
                d_countries = d.split('_')[2].split('-')
                for vc in v_countries: # multiple nationalities per person possible
                    _vc = vc.strip()
                    if _vc == '?':
                        unknown_country = True
                    for dc in d_countries:
                        _dc = dc.strip()
                        all_defendants_countries.append(_dc)
                        if _dc == '?':
                            unknown_country = True
                            defendant_unknown_country = True
                            continue # skip this defendant, no point comparing with victim or case country
                        if _vc == _dc:
                            country_match_found = True # any one victim is from the same country as any one defendant
                        # check if defendant country matches case country
                        country_code = country_citizen[_dc]
                        case_country = df.loc[i, 'country']
                        if re.search(country_code, case_country, re.IGNORECASE):
                            defendant_country_match_case = True


        if country_match_found: # if any one victim is from the same country as any one defendant
            df.loc[i, 'victim_defendant_same_country'] = 'Yes'
            stats['victim_defendant_same_country']['At least one match'] += 1
        elif unknown_country:
            df.loc[i, 'victim_defendant_same_country'] = 'Country not provided'
            stats['victim_defendant_same_country']['Country not provided'] += 1
        else:
            df.loc[i, 'victim_defendant_same_country'] = 'No match'
            stats['victim_defendant_same_country']['No match'] += 1
    else: # a '-' in a cell indicates that the field was not available in the html
        df.loc[i, 'victim_defendant_same_country'] = 'Field missing'
        stats['victim_defendant_same_country']['Entire field unavailable'] += 1

    if defendant_country_match_case: # if any one defendant's country matches case's country
        stats['defendant_country_match_case']['At least one match'] += 1
        df.loc[i, 'defendant_country_match_case'] = 'Yes'
    elif df.loc[i, 'country'] == '-' or defendants == '-':
        stats['defendant_country_match_case']['Entire field unavailable'] += 1
        df.loc[i, 'defendant_country_match_case'] = 'Field missing'
    elif defendant_unknown_country: # if there is no match and at least one defendant's country is unknown
        stats['defendant_country_match_case']['Defendant country unknown'] += 1
        df.loc[i, 'defendant_country_match_case'] = 'Defendant country unknown'
    else: # if no match and all defendant's country and case country are known
        stats['defendant_country_match_case']['No match'] += 1
        df.loc[i, 'defendant_country_match_case'] = 'No match'

    # check if imprisonment >= 4 years
    imprisonment = df.loc[i, 'imprisonment']
    life = re.search('life', imprisonment, re.IGNORECASE)
    if life:
        df.loc[i, 'serious_crime'] = 'Yes'
    else:
        terms = re.findall('(\d+) year', imprisonment)
        for y in terms:
            if int(y) >= 4:
                df.loc[i, 'serious_crime'] = 'Yes'
                break

    if imprisonment == '-':
        stats['imprisonment']['no info'] += 1
    elif df.loc[i, 'serious_crime'] == 'Yes':
        stats['imprisonment']['any has serious crime'] += 1
    else:
        stats['imprisonment']['all no serious crime'] += 1
        df.loc[i, 'serious_crime'] = 'No'


    # check if case meets criteria for human trafficking
    acts = (df.loc[i, 'acts'] != '-')
    means = (df.loc[i, 'means'] != '-')
    purpose = (df.loc[i, 'purpose'] != '-')
    transnational = re.search('Transnational', df.loc[i, 'form_transnational'], re.IGNORECASE)
    organised = re.search('Organized Criminal Group', df.loc[i, 'form_organised'], re.IGNORECASE)
    num_criteria_met = 0

    if acts:
        num_criteria_met += 1
        criteria_count[0] += 1
    if (means or df.loc[i, 'victims_type'] == 'all children'):
        num_criteria_met += 1
        criteria_count[1] += 1
    if purpose:
        num_criteria_met += 1
        criteria_count[2] += 1
    if transnational:
        num_criteria_met += 1
        criteria_count[3] += 1
    if organised:
        num_criteria_met += 1
        criteria_count[4] += 1
    if (df.loc[i, 'serious_crime'] == 'Yes'):
        num_criteria_met += 1
        criteria_count[5] += 1

    if num_criteria_met == 6:
        df.loc[i, 'meet_criteria'] = 'Yes'
    df.loc[i, 'num_criteria_met'] = num_criteria_met
    case_total_criteria_met[num_criteria_met] += 1

    # check if keywords for each criteria found in keyword section
    keyword_section_match_count = 0
    if re.search('\[k', df.loc[i, 'acts'], re.IGNORECASE):
        keyword_section_match_count += 1
    if re.search('\[k', df.loc[i, 'means'], re.IGNORECASE):
        keyword_section_match_count += 1
    if re.search('\[k', df.loc[i, 'purpose'], re.IGNORECASE):
        keyword_section_match_count += 1
    if transnational:
        keyword_section_match_count += 1
    if organised:
        keyword_section_match_count += 1
    if df.loc[i, 'serious_crime'] == 'Yes':
        keyword_section_match_count += 1

    df.loc[i, 'keyword_section_match_count'] = keyword_section_match_count

## End loop for each case


# Plot graphs
plt.bar(range(6), criteria_count, tick_label=['acts','means','purpose','transnational','organised','seriousness'])
plt.title('criteria met count')
plt.savefig('outputs/criteria met count.png')

plt.figure()
plt.bar(range(7), case_total_criteria_met)
plt.title('case_total_criteria_met')
plt.savefig('outputs/case_total_criteria_met.png')

male_ages.sort()
female_ages.sort()
child_ages.sort()
unknown_ages.sort()

plt.figure()
df['keyword_section_match_count'].plot(kind='hist', title ="keyword_section_match_count", figsize=(15, 10), fontsize=14)
plt.savefig('outputs/keyword_section_match_count.png')


with open('outputs/gender_ages.txt','w') as f:
    f.write('male_ages\n')
    f.write(','.join(str(age) for age in male_ages))
    f.write('\nfemale_ages\n')
    f.write(','.join(str(age) for age in female_ages))
    f.write('\nchild_ages\n')
    f.write(','.join(str(age) for age in child_ages))
    f.write('\nunknown_ages\n')
    f.write(','.join(str(age) for age in unknown_ages))

fig, axes = plt.subplots(2,2)
fig.subplots_adjust(hspace=0.5, wspace=0.3)
axes[0,0].hist(male_ages, bins=[-1, 0] + list(range(18,100,1)))
axes[0,0].title.set_text('Male ages count')
# plt.savefig('outputs/Male ages count.png')
axes[0,1].hist(female_ages, bins=[-1, 0] + list(range(18,100,1)))
axes[0,1].title.set_text('Female ages count')
# plt.savefig('outputs/Female ages count.png')
axes[1,0].hist(child_ages, bins=list(range(-1,18,1))+[50])
axes[1,0].title.set_text('Child ages count')
# plt.savefig('outputs/Child ages count.png')
axes[1,1].hist(unknown_ages)
axes[1,1].title.set_text('Unknown gender ages count')
# plt.savefig('outputs/Unknown gender ages count.png')
plt.savefig('outputs/gender ages count.png')


# Print stats
stats['victim_gender']['male'] = len(male_ages)
stats['victim_gender']['female'] = len(female_ages)
stats['victim_gender']['child'] = len(child_ages)
stats['victim_gender']['unknown'] = len(unknown_ages)


for measure in stats['victims_type']:
    stats['victims_type'][measure] = (df.loc[:, 'victims_type']==measure).sum()
print('total cases', len(df.index))
print('meet_criteria', np.sum(df.loc[:, 'meet_criteria'] == 'Yes'), '\n')
for field in stats:
    total = 0
    for measure in stats[field]:
        print(field, ':', measure, '=', stats[field][measure])
        total += stats[field][measure]
    print(field, ':', 'total', '=', total, '\n')

df.to_csv('dataset analysed.csv')
