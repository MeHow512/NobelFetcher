# Nobel Data Fetcher

The repository contains script that allows you to fetch information about Nobel Prize winners from https://www.nobelprize.org. 
It uses API version 2, which was released by the previously mentioned organization. API Key is not required. Retrieves 
data about the winners who received the Nobel award in selected in config years.

The data downloaded includes name, family name, gender, date of birth, link to Wikipedia and all Nobel Prizes won by
Nobel Prize winner (including data about: category, prize status, motivation and award year). Awards received by 
organizations are skipped.

By default, data of winners from 2002-2024 are downloaded.

### RUNNING ( Windows recommended )
1. Download repository from GitHub.
2. Make sure you have at least python version **3.12**.
3. Create **venv** environment in repository root directory by command:
```shell
python -m venv venv
```
>If you are using linux system you may need to use **python3** instead of **python** in above command.

4. Activate created environment by using below selected command:

WINDOWS:
```shell
venv\Scripts\activate
```

LINUX:
```shell
source venv/bin/activate
```

5. Install requirements by using below command:
```shell
pip install -r requirements.txt
```

6. Navigate to app/ directory and run script by using below command with additional parameters:
```shell
python app.py [-h] [-v] [--json] [--excel]
```

###### Parameters:

- -h --> Show help information about script
- -v --> Sets the verbosity level of the output logs from -v to -vvvvv, where -v is the DEBUG level of the logs
and -vvvvv is the CRITICAL level (recommended -vv to log from INFO level)
- --json --> The flag used allows you to save data downloaded from the API to a .json file
- --excel --> The flag used allows you to save data downloaded from the API to a .xlsx file

### ADDITIONAL INFORMATION
- If you want to change the range of years from which you want to download data, you can do it in the config.toml file,
in the api_params section, where you should set nobelPrizeYear (starting date) and yearTo (end date).
- Please remember that the minimum year that can be selected is 1901 (max data coverage from the API). 
- Also remember that the larger the time interval, the more nested the data will be in the chart, which may affect 
their readability.