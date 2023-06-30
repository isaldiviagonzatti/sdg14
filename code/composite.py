import numpy as np
import pandas as pd


def compositeDF(alpha, df, sigma):
    # define the generalized mean function
    # the function works with dataframe columns
    try:
        return (alpha * df ** ((sigma - 1) / sigma)).sum(axis=1) ** (
            sigma / (sigma - 1)
        )
    except:
        pass


def compositeMC(df, years=[2012], simulations=10_000):
    # define the Monte Carlo simulation function
    # the function transforms the dataframe into a numpy array for each country and year
    # then it loops through all elasticity values and calculates the composite
    # it returns a dataframe with the mean and std of the composite for each country-year pair
    if type(df) != pd.DataFrame:
        raise Exception("The df must be a pandas DataFrame")
    if type(years) != list:
        raise Exception("The years must be a list")
    if type(simulations) != int:
        raise Exception("The simulations must be an integer")
    if df.index.nlevels != 2:
        raise Exception("The df must have two levels of index")
    if df.shape[1] < 2:
        raise Exception("The targets must have at least two columns")
    else:
        # define seed to reproduce, random uniform elasticity, and number of simulations
        np.random.seed(8)
        elasticity = np.random.uniform(0, 1, simulations)
        scoresGoal = pd.DataFrame(columns=["Country", "Year", "meanScore", "stdScore"])
        # loop through all countries and years,
        # calculate the composite with different elasticity
        for year in years:
            for country in df.index.get_level_values(0).unique():
                scoreMC = np.array([])
                targetArray = df.loc[country, year].to_numpy()
                alpha = 1 / len(targetArray)
                # ignore divide by zero error
                with np.errstate(divide="ignore"):
                    # loop through all elasticity values, append to list of scores
                    for sigma in elasticity:
                        score = (alpha * sum(targetArray ** ((sigma - 1) / sigma))) ** (
                            sigma / (sigma - 1)
                        )
                        scoreMC = np.append(scoreMC, score)
                        # remove inf values
                        scoreMC = scoreMC[~np.isinf(scoreMC)]
                # calculate mean and std, append to dataframe
                mean, std = np.mean(scoreMC), np.std(scoreMC)
                scoresGoal.loc[len(scoresGoal)] = [country, year, mean, std]
        scoresGoal.set_index(["Country", "Year"], inplace=True)
        return scoresGoal
