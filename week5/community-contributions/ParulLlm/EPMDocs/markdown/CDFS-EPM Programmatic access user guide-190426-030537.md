## EPM Programmatic access user guide 

## Overview 

We export the financial and planning data from Oracle EPM Cloud Planning to Expedia Group Data Lake (EGDL) tables and make it available to consumers for the programmatic access. The process is automated using scheduled airflow jobs, Oracle Integrations, and cloud storage. 

Oracle Integration Cloud (OIC) enables automated data export from Oracle EPM Cloud to AWS S3 EG Data Lake by orchestrating data extraction, transformation, and storage processes. This integration helps maintain backups, enable advanced analytics, and ensure seamless data movement between cloud platforms. 

## Access 

We have implemented a security model(Row-Level Access) to grant appropriate EPM cloud data access to the consumers in EGDL test and prod environments. For this we've created 3 security groups (request access to one of the below security groups based on your - requirements) 

epm-access-all → Access to both b2b and b2c brands 

- epm-access-b2c → Access to only b2c brands 

- epm-access-b2b → Access to only b2b brands 

- ‘epm-access-b2c' and 'epm-access-b2b' are semi private groups, so you should be able to request access to these and we will review and approve it. If you think you need access to 

- 'epm-access-allʼ group (private), please reach out to @amarathe or @Nate Bannick so that 

we can add you. Note that you should be part of only one SG. 

## EGDL tables 

## EPM Cube data tables - 

- 1 select * from egdp_prod_finance_analytics.epm_fin_plan_cube_table; 2 select * from egdp_prod_finance_analytics.epm_vtr_plan_cube_table; 

## Dimension meta data tables - 

- 1 select * from egdp_prod_finance_analytics.epm_account_metadata_table; 

- 2 select * from egdp_prod_finance_analytics.epm_brand_metadata_table; 

- 3 select * from egdp_prod_finance_analytics.epm_businessmodel_metadata_table; 

- 4 select * from egdp_prod_finance_analytics.epm_channel_metadata_table; 

- 5 select * from egdp_prod_finance_analytics.epm_company_metadata_table; 

- 6 select * from egdp_prod_finance_analytics.epm_costcenter_metadata_table; 

- 7 select * from egdp_prod_finance_analytics.epm_currency_metadata_table; 8 select * from egdp_prod_finance_analytics.epm_day_metadata_table; 9 select * from egdp_prod_finance_analytics.epm_hsp_metric_metadata_table; 

- 10 select * from egdp_prod_finance_analytics.epm_intercompany_metadata_table; 11 select * from egdp_prod_finance_analytics.epm_lineitem_metadata_table; 

- 12 select * from egdp_prod_finance_analytics.epm_location_metadata_table; 

- 13 select * from egdp_prod_finance_analytics.epm_period_metadata_table; 14 select * from egdp_prod_finance_analytics.epm_planelement_metadata_table; 15 select * from egdp_prod_finance_analytics.epm_product_metadata_table; 16 select * from egdp_prod_finance_analytics.epm_scenario_metadata_table; 17 select * from egdp_prod_finance_analytics.epm_sec_attribute_metadata_table; 18 select * from egdp_prod_finance_analytics.epm_smart_lists_metadata_table; 19 select * from egdp_prod_finance_analytics.epm_timingcard_metadata_table; 20 select * from egdp_prod_finance_analytics.epm_version_metadata_table; 21 select * from egdp_prod_finance_analytics.epm_view_metadata_table; 22 select * from egdp_prod_finance_analytics.epm_years_metadata_table; 

## Fxrates table 

- 1 select * from egdp_prod_finance_analytics.epm_fxrates_table 

Note: When dealing with dimension metadata tables, since the same dimensions can exist in multiple hierarchies, you need to exclude the shared hierarchy elements from your results to get - the primary hierarchy results. To do that, you can add this filter to your query data_storage <> 'shared' 

Data sets 

- The below datasets can be fetched from 

egdp_prod_finance_analytics.epm_fin_plan_cube_table 

egdp_prod_finance_analytics.epm_vtr_plan_cube_table 

All the below jobs are scheduled based on PST and shouldnʼt be affected by Day light savings. 

|Data set|Cube|Criteria to fetch|Published|Schedule|
|---|---|---|---|---|
|Actuals|FIN_PLA<br>N|scenario = Actual<br>version = Final|After each consolidation<br>monthly|Scheduled for WD1,<br>WD2 & WD3 of each<br>month at 11 PM PST.<br>Adhoc - after the<br>consolidation|
|Plan|FIN_PLA<br>N &<br>VTR_PLA<br>N|scenario = Plan<br>version = Final|After the Plan has been<br>locked|Adhoc - Once after<br>the Plan has been<br>finalized|
|Finalized<br>Forecast|FIN_PLA<br>N &|scenario =<MMM><br>Forecast (Ex:Jan|After the current month<br>forecast has been locked|Adhoc - Once a<br>month after the|



|||VTR_PLA<br>N|Forecast)<br>version =<br><FYxx>_Archive (Ex:<br>FY25_Archive)||forecast has been<br>finalized||
|---|---|---|---|---|---|---|
||Active<br>Forecast|FIN_PLA<br>N &<br>VTR_PLA<br>N|scenario = Forecast<br>version =<br>Working_Prior|Ongoing basis - daily|Scheduled daily at:<br>1st run - 7:30 AM<br>PST<br>2nd run - 11:30 PM<br>PST||
||Dimension<br>s<br>Metadata||from dimension<br>tables above|Daily|Scheduled daily at 11<br>PM PST||
||Fxrates|FIN_PLA<br>N|Archived forecast<br>rates:<br>scenario =<br><MMM><br>Forecast (Ex:<br>Jan Forecast)<br>version =<br><FYxx>_Archive<br>(Ex:<br>FY26_Archive)<br>Working forecast<br>rates:<br>scenario =<br>NoScenario<br>version =<br>NoVersion<br>Spot rates:<br>scenario =<br>Actual<br>version = Final|Archived forecast rates -<br>adhoc<br>Working forecast rates -<br>Daily<br>Spot rates→Whenever<br>actuals are loaded on a<br>monthly basis|Archived forecast<br>rates will be<br>updated as part of<br>loading the<br>Archived forecast<br>data for any<br>locked period.This<br>will be run adhoc<br>whenever the<br>forecastis locked.<br>Spot rates will be<br>loaded as part of<br>loading the<br>Actuals data for a<br>period.This will be<br>run whenever the<br>actuals are loaded<br>during the first few<br>working days of<br>the month.<br>Working forecast<br>rates will be<br>updated daily||



**==> picture [382 x 238] intentionally omitted <==**

twice as part of loading the daily active forecast data. The active forecast job will run twice a day like mentioned above at: 1st run - 7:30 AM PST 2nd run - 11:30 PM PST 

## Data Available in EGDL 

## For FIN_PLAN: egdp_prod_finance_analytics.epm_fin_plan_cube_table 

- 

- Actuals Data from FY24 is available 

- 

- Plan FY25 plan data is available 

- - 

- Active Forecast Working_Prior data for FY25,FY26 is available (this job is scheduled daily will get the up-to-date forecast data) 

- 

- Archived Forecast Oct and Nov Forecast data is available for FY25,FY26 

## For VTR_PLAN: egdp_prod_finance_analytics.epm_vtr_plan_cube_table 

- 

- Plan FY25 plan data is available 

- - 

- Active Forecast Working_Prior data for FY25,FY26 is available (this job is scheduled daily will get the up-to-date forecast data) 

- 

- Archived Forecast Jan, Apr, Jun Forecast is available for FY25,FY26 

## For Fxrates: egdp_prod_finance_analytics.epm_vtr_plan_cube_table 

- FY26_Archive fxrates for Jan,Feb & Mar forecast are loaded. 

## FAQ: 

- How to access parent hierarchy for a particular dimension element? 

   - We have parent columns for each row in each meta data table starting from parent_1…upto parent_15 where parent_1 being the top level parent and it flows down the hierarchy. We also 

have alias columns for each parent (parent_1_alias,….parent_15_alias) which will be useful to 

find the parent names. We also have parents column at the end which stores the list of all 

parents for that particular dimension element with first value in the array being the top level parent until the direct parent of the element. 

- How to get the total gbv or some metric value for a particular brand, product or location when 

- i donʼt know the fusion values? 

   - You can join epm_fin_plan_cube_table with the appropriate metadata table 

   - epm_<xxx>_metadata_table which will have more data about that particular dimension 

   - to get the needed results. 

## Support Contact: 

Please reach out in #programmatic-access slack channel for any questions. 

