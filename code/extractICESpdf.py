import os
import pandas as pd
import PyPDF2
import re
import camelot
import numpy as np

# define stock list
fishStock = []
for file in os.listdir("../dataTemp/icesPDFs"):
    if file.endswith(".pdf"):
        fishStock.append(os.path.splitext(file)[0])

extractedStock = []
for file in os.listdir("../dataTemp/icesAdviceExtracted"):
    if file.endswith(".csv"):
        extractedStock.append(os.path.splitext(file)[0])
fishStock = [x for x in fishStock if x not in extractedStock]


def read_tables(pages, fish):
    tables = camelot.read_pdf(
        "../dataTemp/icesPDFs/{}.pdf".format(fish),
        pages=pages,
        backend="poppler",
        # flavor='stream',
        # # table_areas accepts strings of the form x1,y1,x2,y2 where (x1, y1) -> top-left and (x2, y2)
        # table_area=['0,600,590,700'],
        # iterations=1,
        line_scale=30,
        # split_text=True,
        strip_text=["#", "^", "<", "-", "≤", "***", "\n"],
    )
    return tables


notExtracted = []
for fish in fishStock:
    print("Extracting", fish)
    # get page number in which Table 6 lies, and also get the next one as tables can span two oages
    obj = PyPDF2.PdfFileReader("../dataTemp/icesPDFs/{}.pdf".format(fish))

    pgno = obj.getNumPages()

    # in some pdfs the Table 6 has more than one space between Table and 6
    s = "Table[ ]{1,}6"
    for i in range(0, pgno):
        PgOb = obj.getPage(i)
        Text = PgOb.extractText()
        if re.search(s, Text):
            pages = str(i + 1) + "," + str(i + 2) + "," + str(i + 3)
            print("Pages", pages)
            break
    try:
        tables = read_tables(pages, fish)
    except:
        try:
            tables = read_tables(pages[:-2], fish)
        except:
            tables = read_tables(pages[:-4], fish)
    # read tables with Camelot. Using backend="poppler" as Ghostscript is not working for me
    # table_area is not providing the expected results
    # iterations had no effect for me
    # delete tables before the first table in list that corresponds to table 6 (Advice)
    # sometimes table 6 is not the Advice table
    try:
        firstAdvice = [
            i
            for i, elem in enumerate(tables)
            if any(
                "ICES advice" in string for string in tables[i].df.iloc[0, :].to_list()
            )
        ][0]
        tables = tables[firstAdvice:]
    except:
        print("No ICES advice in table 6, check the pdf for", fish)
        notExtracted.append(fish)
        continue

    # filter tables by two conditions:
    # [0][0] is numeric and len(columns) is equal to the len(first table 6)
    # or the first row is equal to the first row of the first table 6
    filterTableSix = [
        i
        for i, elem in enumerate(tables)
        if (
            pd.to_numeric(tables[i].df[0].str.extract("(\d+)")[0][0], errors="coerce")
            > 0
            and len(tables[i].df.columns) == len(tables[0].df.columns)
        )
        or tables[i].df.iloc[0, :].equals(tables[0].df.iloc[0, :]) == True
    ]
    tableSix = [tables[i].df for i in filterTableSix]
    tableSix = pd.concat(tableSix).reset_index(drop=True)
    # fix table
    icesTable = tableSix.copy()
    icesTable.columns = icesTable.iloc[0, :]
    icesTable = icesTable[1:].reset_index(drop=True)
    icesTable["fish"] = fish
    # sometimes the columns Year and ICES advice (text) don't split, we strip the text
    icesTable["Year"] = icesTable["Year"].str.extract("(\d+)", expand=False)
    icesTable = icesTable[icesTable["Year"].astype(str).str.isnumeric()]

    # sometimes there is more than one space between the words in the columns
    icesTable.rename(
        columns=lambda x: re.sub(r" +", " ", x).strip(), inplace=True
    )  # '[^a-zA-Z]+'

    # replace columns names
    dictCol = {
        "(?=.*[Cc]atch)(?=.*[Aa]dvice)": "SAD",
        "(?=.*[Ll]anding)(?=.*[Aa]dvice)": "SAD_landings",
        "(?=.*TAC)": "TAC",
        "(?=.*ICES)(?=.*[Ll]anding)": "Landings",
        "(?=.*ICES)(?=.*[Cc]atch)": "Catches (pdfs)",
        "(?=.*ICES)(?=.*[Dd]iscards)": "Discards",
    }

    for key, value in dictCol.items():
        countCol = []
        for i in range(len(icesTable.columns.to_list())):
            count = bool(re.search(key, icesTable.columns[i]))
            countCol.append(count)
        # if more than one column name matches the regex, we don't rename them
        if countCol.count(True) == 1:
            for i in range(len(icesTable.columns.to_list())):
                if bool(re.search(key, icesTable.columns[i])) == True:
                    icesTable.rename(
                        columns={icesTable.columns[i]: value}, inplace=True
                    )
        elif countCol.count(True) > 1 and "san.sa" not in fish:
            print(
                "More than one column name matches the regex, check the table for", fish
            )
            break
    if countCol.count(True) > 1 and "san.sa" in fish:
        continue
    # fix numeric columns
    numericCol = [
        "SAD",
        "SAD_landings",
        "TAC",
        "Landings",
        "Year",
        "Catches (pdfs)",
        "Discards",
    ]
    for col in icesTable.columns:
        if col in numericCol:
            # strip spaces between numbers
            icesTable[col] = icesTable[col].replace({" ": ""}, regex=True)
            # for cases in which there is an explanation of the number, we strip it
            icesTable[col] = icesTable[col].str.split("(").str[0]
            icesTable[col] = icesTable[col].apply(pd.to_numeric, errors="coerce")

    icesTable = icesTable.replace({"": np.nan})
    # if there is no SAD catch, we use SAD_landings
    if "SAD_landings" in icesTable.columns:
        icesTable["SAD"] = icesTable["SAD"].fillna(icesTable["SAD_landings"])

    # define catches as landing + discards
    if "Landings" in icesTable.columns and "Discards" in icesTable.columns:
        icesTable["catchesCal"] = icesTable["Landings"].fillna(0) + icesTable[
            "Discards"
        ].fillna(0)

    # if there is no ICES Catches, we use catchCal
    if "Catches (pdfs)" in icesTable.columns and "catchesCal" in icesTable.columns:
        icesTable["Catches (pdfs)"] = icesTable["Catches (pdfs)"].fillna(
            icesTable["catchesCal"]
        )
    else:
        if "catchesCal" in icesTable.columns:
            icesTable["Catches (pdfs)"] = icesTable["catchesCal"]

    icesTable.reset_index(drop=True, inplace=True)

    # Sandeel case
    if "san.sa" in fish:
        try:
            icesTable = icesTable.loc[
                :, ~icesTable.columns.str.contains("(?=.*[Tt]otal)(?=.*[Cc]atch)")
            ]
            icesCatches = icesTable.columns.str.contains("(?=.*ICES)(?=.*[Cc]atch)")
            if icesCatches.sum() > 1:
                icesTable.iloc[:, np.where(icesCatches)[0][1]].fillna(
                    icesTable.iloc[:, np.where(icesCatches)[0][0]], inplace=True
                )
                icesTable = icesTable.drop(
                    columns=[icesTable.iloc[:, np.where(icesCatches)[0][0]].name]
                )
                icesTable = icesTable.rename(
                    columns={
                        icesTable.iloc[
                            :, np.where(icesCatches)[0][0]
                        ].name: "Catches (pdfs)"
                    }
                )
            else:
                icesTable = icesTable.rename(
                    columns={
                        icesTable.iloc[
                            :, np.where(icesCatches)[0][0]
                        ].name: "Catches (pdfs)"
                    }
                )
        except:
            pass
    # check if all years were read correctly by Camelot
    checkYear = pd.Series(
        np.arange(icesTable.Year.iloc[0], icesTable.Year.iloc[-1] + 1)
    )
    missingYear = checkYear[~checkYear.isin(icesTable.Year)].to_list()
    if missingYear:
        allYears = pd.DataFrame(
            list(range(min(icesTable.Year), max(icesTable.Year + 1))), columns=["Year"]
        )
        icesTable = (
            icesTable.merge(allYears, how="outer", on="Year")
            .sort_values(by="Year")
            .reset_index(drop=True)
        )
        icesTable["missingYear"] = np.where(icesTable.fish.isnull(), 1, np.nan)
        print("Years", missingYear, "were not read correctly")
    else:
        print("All years were read correctly")

    # check for years that were not read because there is a SAD range
    if "SAD" in icesTable.columns:
        specialYear = []
        icesTable["missingSAD"] = np.nan
        for value in range(len(icesTable["SAD"]))[1:-1]:
            if (
                np.isnan(icesTable["SAD"][value])
                and ~np.isnan(icesTable["SAD"][value - 1])
                and ~np.isnan(icesTable["SAD"][value + 1])
            ):
                specialYear.append(value)
                icesTable.loc[value, "missingSAD"] = 1
        if specialYear != []:
            print(
                "Year(s)",
                icesTable["Year"][specialYear].values.tolist(),
                "is a special case",
            )
        else:
            print("All years have a specific SAD value")
    else:
        icesTable.set_index("fish", inplace=True)
        icesTable.to_csv("../dataTemp/icesAdviceExtracted/{}.csv".format(fish))
        print("ICES advice extracted for", fish)
        continue
    # add columns from excel and reorganize
    try:
        excelTable = icesTable.reindex(
            [
                "fish",
                "Most recent assessment with corresponding report",
                "Year",
                "Catches (stockass)",
                "SAD",
                "TAC",
                "Catches (pdfs)",
                "done?",
                "report",
                "SAD_landings",
                "Landings",
                "Discards",
                "catchesCal",
                "missingYear",
                "missingSAD",
            ],
            axis=1,
        )
    except:
        icesTable.set_index("fish", inplace=True)
        icesTable.to_csv("../dataTemp/icesAdviceExtracted/{}.csv".format(fish))
        print("ICES advice without column format extracted for", fish)
        continue

    # icesTable = icesTable.replace('','N/A')
    excelTable.set_index("fish", inplace=True)
    excelTable.to_csv("../dataTemp/icesAdviceExtracted/{}.csv".format(fish))
    print("ICES advice extracted for", fish)

if "spr.27.3a4bis" not in extractedStock:
    # sum of spr.27.3a and spr.27.4
    spr4 = pd.read_csv("../dataTemp/icesAdviceExtracted/spr.27.4.csv")
    spr3a = pd.read_csv("../dataTemp/icesAdviceExtracted/spr.27.3a.csv")
    col_list = spr3a.columns.tolist()
    spr4, spr3a = (
        df.set_index(["Year"]).drop(columns=["fish"]) for df in [spr4, spr3a]
    )
    spr3a
    spr3aHist = spr3a.add(spr4, fill_value=0)
    spr3aHist["fish"] = "spr.27.3a4"
    spr3aHist.reset_index(inplace=True)
    spr3aHist = spr3aHist[col_list]
    spr3aHist.to_csv("../dataTemp/icesAdviceExtracted/spr.27.3a4bis.csv", index=False)

# concat all the stock extracted
listStock = os.listdir("../dataTemp/icesAdviceExtracted/")
listStock = ["../dataTemp/icesAdviceExtracted/" + s for s in listStock]
allStock = pd.concat([pd.read_csv(f) for f in listStock])
allStock.to_csv("../dataTemp/adviceExtracted.csv", index=False)

notExtracted = pd.DataFrame(notExtracted, columns=["fish"])
notExtracted.to_csv("../dataTemp/ICESnotExtracted.csv", index=False)
