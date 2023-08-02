import numpy as np
import pandas as pd


def compositeDF(alpha, df, sigma):
    """
    This function calculates the composite for a given dataframe using the generalized mean
    Each column of the dataframe is an indicator, each row is a country-year
    alpha: the weight of each target
    df: the dataframe with the targets
    sigma: the elasticity value
    """
    try:
        return (alpha * df ** ((sigma - 1) / sigma)).sum(axis=1) ** (
            sigma / (sigma - 1)
        )
    except:
        pass


def compositeMC(df=pd.DataFrame, years=[2012], simulations=10_000):
    """
    Monte Carlo simulation function for the composite indicator.
    The function transforms the dataframe into a numpy array for each country and year.
    Then it loops through all elasticity values and calculates the composite.
    It returns a dataframe with the mean and std of the composite for each country-year pair

    df: the dataframe with the targets, index must be country-year
    years: the years to calculate the composite
    simulations: the number of simulations to run
    """
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
        scoresGoal = pd.DataFrame(columns=["Country", "Year", "scoreMean", "scoreStd"])
        # loop through all countries and years,
        # calculate the composite with different elasticity
        for year in years:
            for country in df.index.get_level_values("Country").unique():
                try:
                    scoreMC = np.array([])
                    targetArray = df.loc[country, year].to_numpy()
                    alpha = 1 / len(targetArray)
                    # ignore divide by zero error
                    with np.errstate(divide="ignore"):
                        # loop through all elasticity values, append to list of scores
                        for sigma in elasticity:
                            score = (
                                alpha * sum(targetArray ** ((sigma - 1) / sigma))
                            ) ** (sigma / (sigma - 1))
                            scoreMC = np.append(scoreMC, score)
                            # remove inf values
                            scoreMC = scoreMC[~np.isinf(scoreMC)]
                    # calculate mean and std, append to dataframe
                    mean, std = np.mean(scoreMC), np.std(scoreMC)
                    scoresGoal.loc[len(scoresGoal)] = [country, year, mean, std]
                except KeyError:
                    continue
        scoresGoal.set_index(["Country", "Year"], inplace=True)
        return scoresGoal
