# SDG 14 Europe

Repository for the paper Progress of EU coastal states against sustainable development goal 14

##Usage

You can run any file and it should work out of the box. If not, check that the working directory is set to the parent folder of the project "SDG14". 

If you run the line 
```python
os.chdir('..')
```
twice, the wd will go one folder out.

## Organisation of folders

Data contains all raw data as downloaded from the source

Code contains the code to analyse the data

Output contains the analysed and summarised data and the generated plots

## Sources:

[OfficialNominalCatches](https://www.ices.dk/data/dataset-collections/Pages/Fish-catch-and-stock-assessment.aspx)

[stockAssesment](https://standardgraphs.ices.dk/stockList.aspx)

[recordTACs](https://griffincarpenter.org/reports/european-fishing-quotas-2001-2021/)

[icesTACcomparison](https://neweconomics.org/campaigns/landing-the-blame)

Gross Nutrient Balance [aei_pr_gnb](https://ec.europa.eu/eurostat/databrowser/view/AEI_PR_GNB__custom_153613/)

Waste Generation [env_wasgen](https://ec.europa.eu/eurostat/databrowser/view/ENV_WASGEN/)

Recovery Rates [ten00062](https://ec.europa.eu/eurostat/databrowser/view/ten00062/default/table?lang=en)

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)