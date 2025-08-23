
# convert CSV representing portfolio into portfolio object

import csv

# fidelity quantity and basis
p_sym = 1
p_quantity = 3
p_basis = 11

# yahoo quantity and basis
#p_sym = 0
#p_quantity = 11
#p_basis = 10


def buildPortfolio(filename):

    portfolio = {}
    count = 0
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            count = count + 1 
            if (count == 1): # skip header row
                continue
                
            q = {}
            q['shares'] = []
            
            if (row[p_sym] in portfolio.keys()):
                q = portfolio[row[p_sym]]
            else:
                portfolio[row[p_sym]] = q

            if (row[p_quantity] == ''):
                row[p_quantity] = '0'
            if (row[p_basis] == ''):
                row[p_basis] = '0'

            clean_basis = row[p_basis].replace('$', '')
            print(clean_basis)
            q['shares'].append([float(row[p_quantity]), float(clean_basis)])
            

    print(portfolio)
    
    return portfolio
