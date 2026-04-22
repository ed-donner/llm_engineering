## EPM Planning and Forecasting Data in EGDL (Programmatic Access) 

Overview 

Current State: 

Future State – Unified Approach: 

- High-Level Architecture EGDL Data Security 

- Airflow jobs: 

- Steps to run an airflow job: EGDL tables: 

- FIN_PLAN Dimensionality 

Key Benefits of the New Approach: 

- Conclusion: 

Requirements Discussion Recording Questions and Discussions 

## Overview 

The data export process involves transferring financial and planning data from Oracle EPM 

Cloud Planning to Expedia Group Data Lake (EGDL). The process is automated using scheduled jobs, Oracle Cound Integrations, and cloud storage. 

Oracle Integration Cloud (OIC) enables automated data export from Oracle EPM Cloud to AWS S3 EG Data Lake by orchestrating data extraction, transformation, and storage processes. This integration helps maintain backups, enable advanced analytics, and ensure seamless data movement between cloud platforms. 

## Current State: 

- Today, we provide Actual and Forecast data extracts to various teams (TPSP, Marketing Analytics Godzilla, eCP, LPS)through multiple methods. 

- Some teams receive data via direct push to SQL Server, while others rely on file-based 

- extracts. 

Additionally, some data is already being published to the Expedia Group Data Lake (EGDL). 

This fragmented approach requires multiple integration points and manual intervention, leading to inefficiencies and potential inconsistencies. 

On Prem EPM Outbound - Call Center/GCO data 

- On Prem EPM Outbound - Channel Extract to EGDL 

- On Prem EPM Outbound - eCP Data Extract 

- On Prem EPM Outbound - LPS Data Extract 

Future State – Unified Approach: 

- In the new system, we will standardize how EPM data is shared by publishing both forecast 

- and actual data for all teams to EGDL. 

- This shift eliminates the need for custom data extracts and manual transfers, providing 

- a single source of truth for financial data. 

## High-Level Architecture 

1. Trigger: The OIC integrations are triggered via a scheduled job in OIC. 

2. Extract Data from Oracle EPM: OIC invokes the EPM Cloud Adapter to execute a Data 

   - Management export jobs that generates a file (CSV, ZIP, or DAT format). 

- ʼ 

- 3. Download Exported File: The generated file is retrieved from EPM s Outbox folder using the EPM Adapter or REST API. 

4. Transformations: By application and use case required transformations will be performed while transforming data from EPM outbox to EG Data Lake. 

5. Upload to AWS S3: The file is sent to AWS S3 EG Data Lake using the Amazon S3 Adapter or REST API. 

6. Data Access: Consumer applications can access the data from EGDL by registering the access pattern via EG Security groups 

7. Monitor & Notify: The integration logs success or failure and notifies relevant stakeholders. The status of schedules and jobs are tracked in the OIC dashboards. 

**==> picture [498 x 121] intentionally omitted <==**

## Data Access and Security 

The data publishing process can support dimension-based security, allowing access restrictions based on user roles and data attributes, such as brand, product or account. 

Hive Tables Access Link 

## Ranger Policy: 

- A Ranger policy defines who can access specific resources and what actions they can perform within Apache Ranger. 

## Table-Level Access: 

- Restricts access at the table level, ensuring only authorized users can view specific datasets. 

## Column-Level Access: 

- Column restrictions and column masking control the visibility of sensitive information based on user roles. 

## Row-Level Access: 

- Row-level filtering enforces access restrictions at a granular level, limiting data visibility based on data attributes such as brand, product, or account. 

## EPM data security in EGDL: 

We have implemented a security model(Row-Level Access) to grant appropriate EPM cloud data access to the consumers in EGDL test and prod environments. For this we've created 3 - security groups 

- epm-access-all → Access to both b2b and b2c brands 

- epm-access-b2c → Access to only b2c brands 

- epm-access-b2b → Access to only b2b brands 

- Gisheeʼs team, Adriana's team and Gogul have been put into epm-access-all 

- Godzila team has been put into epm-access-b2c 

- We will expand these groups as we move on. 

- 'epm-access-b2c' and 'epm-access-b2b' are semi private groups, so one should be able to 

- request access to these and we will review and approve it. If you think you need access to epm-access-all group (private), please reach out to @amarathe or @Hari Gopal Anil so that we can add you. Note that you should be part of only one SG. 

- There is no security in place for fxrates table. 

- Row level filters 

- - - - - fin_plan (prod) https://github.com/eg internal/egdl access control/blob/master/egdp 

prod/policies/rowFilters/epm_fin_plan_userpool_access.json 

- - - - - fin_plan (test) https://github.com/eg internal/egdl access control/blob/master/egdp test/policies/rowFilters/epm_fin_plan_userpool_access.json vtr_plan (prod) - https://github.com/eg-internal/egdl-access-control/blob/master/egdpprod/policies/rowFilters/epm_vtr_plan_userpool_access.json vtr_plan (test) - https://github.com/eg-internal/egdl-access-control/blob/master/egdptest/policies/rowFilters/epm_vtr_plan_userpool_access.json 

## Airflow jobs: 

Access: Join sg-fde-plan-forecasting security group to get access to the below - - airflow jobs askEG Login Page askEG 

## FIN_PLAN: 

## Prod: 

- - - - - - - - Active forecast https://airflow finance planning forecasting.wo eks us east - 1.data.dw.exp aws.net/dags/epm_finplan_active_forecast_export_task/grid 

- Actuals - https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.dw.expaws.net/dags/epm_finplan_actuals_export_task/grid - - - - - - - 

- Archived forecast (adhoc) https://airflow finance planning forecasting.wo eks us - - 

- east 1.data.dw.exp aws.net/dags/epm_finplan_archived_forecast_export_task/grid Plan - https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.dw.expaws.net/dags/epm_finplan_cube_data_export_task/grid 

## Test: 

- - - - - - - - 

- Active forecast https://airflow finance planning forecasting.wo eks us east - 

- 1.data.test.exp aws.net/dags/epm_finplan_active_forecast_export_task/grid Actuals - https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.test.expaws.net/dags/epm_finplan_actuals_export_task/grid - - - - - - - 

- Archived forecast (adhoc) https://airflow finance planning forecasting.wo eks us - - 

- east 1.data.test.exp aws.net/dags/epm_finplan_archived_forecast_export_task/grid Plan (adhoc) - https://airflow-finance-planning-forecasting.wo-eks-us-east- 

- 1.data.test.exp aws.net/dags/epm_finplan_cube_data_export_task/grid 

## Airflow variables for both Prod and Test environments: 

## Active forecast: 

- “fin-plan-data-load-image-version” → docker image version (github commit sha) 

- “fin-plan-active-forecast-scenario” → Forecast 

- “fin-plan-active-forecast-version” → Working_Prior 

- “fin-plan-active-forecast-years” → FY26,FY27 

- “fin-plan-active-forecast-period” → Yeartotal 

## Actuals: 

- “fin-plan-data-load-image-version” → docker image version (github commit sha) 

- “fin-plan-data-load-actual-scenario” → Actual 

- “fin-plan-data-load-actual-version” → Final 

- “fin-plan-data-load-actual-years” → FY26 

- “fin-plan-data-load-actual-period” → Feb 

## Archived forecast (adhoc): 

- “fin-plan-data-load-image-version” → docker image version (github commit sha) 

- “fin-plan-archived-forecast-scenario” → Feb Forecast 

- “fin-plan-archived-forecast-version” → FY26_Archive 

- “fin-plan-archived-forecast-years” → FY26,FY27 

- “fin-plan-archived-forecast-period” → Yeartotal 

## Plan (adhoc): 

- “fin-plan-data-load-image-version” → docker image version (github commit sha) 

- “fin-plan-data-load-scenario” → Plan 

- “fin-plan-data-load-version” → Final 

- “fin-plan-data-load-years” → FY26 

- “fin-plan-data-load-period” → Yeartotal 

Note: Use period as “Yeartotal” if you want to run it for all months. 

## VTR_PLAN: 

## Prod: 

- - - - - - - - Active forecast https://airflow finance planning forecasting.wo eks us east 

- 1.data.dw.exp aws.net/dags/epm_vtrplan_active_forecast_export_task/grid 

- - - - - - Plan & Archived forecast (adhoc) https://airflow finance planning forecasting.wo eks - - - us east 1.data.dw.exp aws.net/dags/epm_vtrplan_cube_data_export_task/grid 

## Test: 

- - - - - - - - Active forecast https://airflow finance planning forecasting.wo eks us east - 1.data.test.exp aws.net/dags/epm_vtrplan_active_forecast_export_task/grid 

- - - us east 1.data.test.exp aws.net/dags/epm_vtrplan_cube_data_export_task/grid 

## Airflow variables for both Prod and Test environments: 

## Active forecast: 

- “vtr-plan-data-load-image-version” → docker image version (github commit sha) 

- “vtr-plan-active-forecast-scenario” → Forecast 

- “vtr-plan-active-forecast-version” → Working_Prior 

- “vtr-plan-active-forecast-years” → FY26,FY27 

- “vtr-plan-active-forecast-period” → Yeartotal 

## Plan & Archived forecast (adhoc): 

- “vtr-plan-data-load-image-version” → docker image version (github commit sha) 

- “vtr-plan-data-load-scenario” → Feb Forecast 

- “vtr-plan-data-load-version” → FY26_Archive 

- “vtr-plan-data-load-years” → FY26,FY27 

- “vtr-plan-data-load-period” → Yeartotal 

## Metadata dimensions: 

Prod - https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.dw.expaws.net/dags/epm_metadata_export_task/grid 

Test - https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.test.expaws.net/dags/epm_metadata_export_task/grid 

## Airflow variables for both Prod and Test environments: 

“epm-metadata-load-image-version” → docker image version (github commit sha) 

## Fxrates: 

Archived forecast rates will be updated as part of loading the Archived forecast data for any archived period. This will be run adhoc whenever the forecast is locked. 

- Working forecast rates will be updated daily twice as part of loading the daily active forecast data. The active forecast job will run twice a day at: 

   - 

   - 1st run 7:30 AM PST 

   - 

   - 2nd run 11:30 PM PST 

But if we want to load/reload just the fxrates, then here are the airflow jobs: 

- Prod - https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.dw.expaws.net/dags/epm_fxrates_export_task/grid 

Test - https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.test.expaws.net/dags/epm_fxrates_export_task/grid 

## Airflow variables for both Prod and Test environments: 

- fxrates-load-image-version  → docker image version (github commit sha) 

- fxrates-load-scenario  → Ex: Mar Forecast 

- fxrates-load-version  → Ex: FY26_Archive 

## Steps to run an airflow job: 

- 1. Navigate to the airflow job that we want to run based on above links or go to home page https://airflow-finance-planning-forecasting.wo-eks-us-east-1.data.dw.exp-aws.net/home 

and click on the desired job. 

2. From the top menu, click on Admin drop down and select Variables 

**==> picture [483 x 162] intentionally omitted <==**

3. Search for the variables that are required to run the desired job and update them as needed based on the criteria. We can update variables by clicking on the ‘Edit Recordʼ button to the left of the variable and saving it. 

**==> picture [488 x 268] intentionally omitted <==**

4. Now go back to the airflow job and click on Play button on the top right. Once the job starts, we can click on the Logs tab to see the airflow logs. We can also find Kubernetes dashboard link, splunk logs link and spark-ui link in the airflow logs for the job we ran. 

**==> picture [488 x 228] intentionally omitted <==**

## Data sets and schedules: 

All the below jobs are scheduled based on PST and shouldnʼt be affected by Day light savings. 

– FIN_PLAN Cube where all sub-models (VTR and Workforce) will integrate their data and users will finalize their Forecasts. 

– VTR_PLAN Cube where daily transaction level data will be loaded to calculate timing cards. 

|Data set|Cube|Criteria to fetch|Published|Schedule|
|---|---|---|---|---|
|Actuals|FIN_PLAN|scenario = Actual<br>version = Final|After each consolidation<br>monthly|Scheduled for<br>WD1,WD2 &<br>WD3 of each<br>month at 11 PM<br>PST.<br>Adhoc - after<br>the<br>consolidation|



||Plan|FIN_PLAN &<br>VTR_PLAN|scenario = Plan<br>version = Final|After the Plan has been<br>locked|Adhoc - Once<br>after the Plan<br>has been<br>finalized||
|---|---|---|---|---|---|---|
||Finalized<br>Forecast /<br>Archived<br>Forecast|FIN_PLAN &<br>VTR_PLAN|scenario =<MMM><br>Forecast (Ex:Jan<br>Forecast)<br>version =<br><FYxx>_Archive (Ex:<br>FY25_Archive)|After the current month<br>forecast has been<br>locked|Adhoc - Once<br>a month after<br>the forecast<br>has been<br>finalized||
||Active<br>Forecast /<br>Working<br>Forecast|FIN_PLAN &<br>VTR_PLAN|scenario = Forecast<br>version =<br>Working_Prior|Ongoing basis - daily|Scheduled<br>daily at:<br>1st run - 7:30<br>AM PST<br>2nd run -<br>11:30 PM<br>PST||
||Dimensions<br>Metadata||from dimension<br>tables above|Daily|Scheduled<br>daily at 11 PM<br>PST||
||Fxrates|FIN_PLAN|Archived forecast<br>rates:<br>scenario =<br><MMM><br>Forecast (Ex:<br>Jan Forecast)<br>version =<br><FYxx>_Archive<br>(Ex:<br>FY26_Archive)<br>Working forecast<br>rates:<br>scenario =<br>NoScenario|Archived forecast rates -<br>adhoc→Whenever<br>archived forecastis<br>loaded on a monthly<br>basis<br>Working forecast rates -<br>Daily<br>Spot rates→Whenever<br>actuals are loaded on a<br>monthly basis|Archived<br>forecast<br>rates will be<br>updated as<br>part of<br>loading the<br>Archived<br>forecast data<br>for any<br>locked<br>period.This<br>will be run<br>adhoc<br>whenever||



||||version =<br>NoVersion<br>Spot rates:<br>scenario =<br>Actual<br>version = Final||the forecast<br>is locked.<br>Spot rates<br>will be<br>loaded as<br>part of<br>loading the<br>Actuals data<br>for a period.<br>This will be<br>run<br>whenever<br>the actuals<br>are loaded<br>during the<br>first few<br>working days<br>of the month.<br>Working<br>forecast<br>rates will be<br>updated<br>daily twice<br>as part of<br>loading the<br>daily active<br>forecast<br>data.The<br>active<br>forecastjob<br>will run twice<br>a day like<br>mentioned<br>above at:<br>1st run - 7:30<br>AM PST||
|---|---|---|---|---|---|---|



**==> picture [411 x 62] intentionally omitted <==**

2nd run - 11:30 PM PST 

## EGDL tables: 

Use egdp_test_finance_analytics schema for test environment and 

egdp_prod_finance_analytics for prod environment. 

## Metadata tables - 

- 1 select * from egdp_prod_finance_analytics.epm_account_metadata_table; 2 select * from egdp_prod_finance_analytics.epm_brand_metadata_table; 3 select * from egdp_prod_finance_analytics.epm_businessmodel_metadata_table; 4 select * from egdp_prod_finance_analytics.epm_channel_metadata_table; 5 select * from egdp_prod_finance_analytics.epm_company_metadata_table; 6 select * from egdp_prod_finance_analytics.epm_costcenter_metadata_table; 7 select * from egdp_prod_finance_analytics.epm_currency_metadata_table; 8 select * from egdp_prod_finance_analytics.epm_day_metadata_table; 9 select * from egdp_prod_finance_analytics.epm_hsp_metric_metadata_table; 

- 10 select * from egdp_prod_finance_analytics.epm_intercompany_metadata_table; 11 select * from egdp_prod_finance_analytics.epm_lineitem_metadata_table; 12 select * from egdp_prod_finance_analytics.epm_location_metadata_table; 13 select * from egdp_prod_finance_analytics.epm_period_metadata_table; 14 select * from egdp_prod_finance_analytics.epm_planelement_metadata_table; 15 select * from egdp_prod_finance_analytics.epm_product_metadata_table; 16 select * from egdp_prod_finance_analytics.epm_scenario_metadata_table; 17 select * from egdp_prod_finance_analytics.epm_sec_attribute_metadata_table; 18 select * from egdp_prod_finance_analytics.epm_smart_lists_metadata_table; 19 select * from egdp_prod_finance_analytics.epm_timingcard_metadata_table; 20 select * from egdp_prod_finance_analytics.epm_version_metadata_table; 21 select * from egdp_prod_finance_analytics.epm_view_metadata_table; 22 select * from egdp_prod_finance_analytics.epm_years_metadata_table; 

## Cube data tables - 

- 1 select * from egdp_prod_finance_analytics.epm_fin_plan_cube_table; 

- 2 select * from egdp_prod_finance_analytics.epm_vtr_plan_cube_table; 

## Fxrates table 

- 1 select * from egdp_prod_finance_analytics.epm_fxrates_table 

## Implementation details: 

- - - - - Github repo https://github.expedia.biz/accounting data engineering/epm data processing 

- - - - fin_plan cube load → https://github.expedia.biz/accounting data engineering/epm data processing/blob/main/module/src/main/scala/com/expediagroup/data/task/FINPlanCubeData LoadTask.scala 

- - - - vtr_plan cube load → https://github.expedia.biz/accounting data engineering/epm data 

processing/blob/main/module/src/main/scala/com/expediagroup/data/task/VTRPlanCubeDat aLoadTask.scala 

- - - dimensions metadata load → https://github.expedia.biz/accounting data engineering/epm - data processing/blob/main/module/src/main/scala/com/expediagroup/data/task/EPMMetaDataLoa dTask.scala 

- - - - fxrates load → https://github.expedia.biz/accounting data engineering/epm data processing/blob/main/module/src/main/scala/com/expediagroup/data/task/FxratesDataLoad Task.scala 

## FIN_PLAN Dimensionality 

**==> picture [512 x 436] intentionally omitted <==**

**----- Start of picture text -----**<br>
Click here to expand...<br>Dimension Description Additional Details<br>Years The Years dimension represents the various plans and<br>actual years where data will be stored.<br>Period<br>Account<br>Brand<br>BusinessMo<br>del<br>Channel<br>Company<br>**----- End of picture text -----**<br>


**==> picture [541 x 721] intentionally omitted <==**

**----- Start of picture text -----**<br>
CostCenter<br>Currency<br>HSP_View The HSP_View dimension created when a cube is enabled<br>for the Sandboxes feature, the following members is<br>created:<br>BaseData is the default member where data is stored<br>when users are NOT working in a sandbox.<br>SandboxData is the place where a user works with data<br>in a sandbox.<br>ConsolidatedData is a dynamically calculated member<br>and will retrieves data from the SandboxData member if<br>it's available. Otherwise, the ConsolidatedData member<br>retrieves data from the BaseData member of the base<br>version.<br>LineItem<br>Location<br>PlanElement<br>Product<br>Scenario<br>Version<br>**----- End of picture text -----**<br>


## 1. Automated & Scalable Data Flow 

## Data movement will be fully automated using scheduled jobs, Oracle Cloud Integrations, and AWS S3, reducing manual efforts. 

## 2. Enhanced Security & Controlled Access 

Ensures secure data transfer with encryption in transit and at rest. 

- Role-based access controls will regulate data consumption. 

Audit logs will provide visibility into data access and modifications. 

## 3. Advanced Analytics & Cross-Platform Accessibility 

- Standardized data availability in EGDL enables teams to perform advanced analytics without manual data wrangling. 

Supports integration with BI tools, ML models, and other analytical platforms. 

## 4. Compliance & Governance 

Adheres to Expedia Groupʼs data security policies and governance standards to ensure regulatory compliance. 

## Conclusion: 

- This transformation streamlines data accessibility, enhances security, and ensures consistency across teams. 

- By leveraging EGDL, we enable faster decision-making and better collaboration across the organization. 

## Requirements Discussion Recording 

Programmatic Access.mp4 

Questions and Discussions 

|Item|Details|Crea<br>ted<br>By|Assigne<br>d<br>To/Team|Response|Status|
|---|---|---|---|---|---|



||1.|Do we need to publish Exchange<br>Rates|@P|@Nick|Yes we would need to<br>publish the rates<br>including the constant<br>currency rates.|CLOSED|
|---|---|---|---|---|---|---|
||||iyoo|Momena|||
|||||h|||
||||sh||||
||||Pan||||
||||t||||
||2.|De we need to publish the<br>Dimension Hierarchy|@Pi|Integrati<br>on Team|We would need to<br>publish the hierarchy<br>possibly from|OPEN|
||||yoos||||
||||h||||
||||||||
||||Pan||||
||||t||||
||3.|Restatement - What will be the<br>strategy to restate plan/forecastin<br>the system.The Plan and Forecast<br>will have to be republished to<br>EGDL when we have a<br>restatement.|@Pi|@Ryan<br>Ward<br>@Nate<br>Bannick|We will have to publish<br>restated Plan and<br>Forecast numbersin<br>EGDL to sync with the<br>system - Nate to review|OPEN|
||||yoos||||
||||h||||
||||||||
||||Pan||||
||||t||||
||4.|Open forecast - Need some way<br>to displayif the forecastis active<br>or locked.A variable that could<br>display the status and be<br>published as a columnin the EGDL|@Pi|Integrati<br>on Team||OPEN|
||||yoos||||
||||h||||
||||||||
||||Pan||||
||||t||||
||5.|For any data published to EGDLit<br>would be helpfulif we have the<br>published timestamp added to<br>each dataset|@Pi|Integrati<br>on Team||OPEN|
||||yoos||||
||||h||||
||||||||
||||Pan||||
||||t||||
||6.|Security and data partitioning<br>requirement|@Pi|@Abhis|Abhishek & Nate to<br>provide access skeleton<br>by EOW|OPEN|
||||yoos|hek|||
||||h|Marathe<br>@Nate<br>Bannick|||
||||Pan||||
||||t||||
||||||||



||7.|System Performance - Do we have<br>any system performance<br>considerations when we are<br>extracting data from the system|@Pi|@Ryan<br>Ward||OPEN||
|---|---|---|---|---|---|---|---|
||||yoos|||||
|||||||||
||||h|||||
||||Pan|||||
||||t|||||
||8.|The GFT Product/Program team<br>will collaborate with all<br>downstream consumers of<br>Hyperion data to educate them on<br>the new Chart of Accounts.Until<br>the hard launch,they will continue<br>receiving data from the on-prem<br>system.All downstream systems<br>must be retrofitted to consume<br>data from EGDL using the new<br>Chart of Accounts before the hard<br>cutover.|@Pi|@Abhis|No action needed,<br>Education to based on<br>guidance from Nick and<br>Nate - Nate to review|OPEN||
||||yoos|hek||||
||||h|Marathe<br>@Nate<br>Bannick||||
|||||||||
||||Pan|||||
||||t|||||
||9|We will be loading data from 2<br>cubes - FIN_PLAN and<br>VTR_PLAN.<br>Monthly actual data will only be<br>for FIN_PLAN.Finalized<br>Forecast,Plan and Active<br>Forecast will be for both<br>FIN_PLAN and VTR_PLAN.<br>4 airflowjobsin total -<br>Active Forecast for FIN_PLAN<br>- scheduled daily<br>Active Forecast for<br>VTR_PLAN - scheduled daily<br>Finalized Forecast,Plan and<br>Monthly Actual for FIN_PLAN<br>- run manually as needed by<br>updating airflow variables<br>accordingly|@M|@Ryan<br>Ward<br>@Piyoo<br>sh Pant|Agreed on these points.|||
||||anoj|||||
||||Gan|||||
||||gul<br>a|||||



Finalized Forecast, Plan and Monthly Actual for FIN_PLAN - run manually as needed by updating airflow variables accordingly Airflow jobs will accept 4 variables for scenario, version, years and period. We will overwrite the data based on partition criteria which will be (scenario,version,years,period) Monthly actual job will only overwrite the same month data if we are running it multiple times during a month. It will not overwrite previous month data since period will be different. Likewise for the other jobs, data will be overwritten only if it matches the above partition criteria BegBalance will be fetched for all the above jobs. Groovy script for copying data from Working to Working_Prior version will be run only for Active Forecast case. Data load criteria from cubes - Account - FIN_PLAN Lvl0descendants of NONFIN, INCMST, Driver_Rates_stats - VTR_PLAN Lvl0descendants of 

Booked_To_Stayed_Metrics - Currency Local_Currency, USD_Constant, USD_GL, USD_Constant_Orig LineItem - FIN_PLAN Total_LineItem (No Lvl0descendants) - VTR_PLAN NoLineItem HSP_View - BaseData - Company Lvl0descendants of All_LedgerCurrency and Timing_Card_LE - PlanElement - FIN_PLAN Total_Plan, Total_Plan_w_CorpFPA_Res erve (No Lvl0descendants) - VTR_PLAN Stayed_Value_or_Amt, Timing_Card_Default_Pct, Timing_Card_Forecast_Appl ied_Pct (No Lvl0descendants) BusinessModel - ILvl0Descendants(Total_Busin essModel) - Brand ILvl0Descendants(Total_Bran d) - Channel ILvl0Descendants(Total_Chan nel) Location - ILvl0Descendants(Total_Loca tion) - Product ILvl0Descendants(Total_Prod 

|||uct)<br>CostCenter<br>FIN_PLAN -<br>ILvl0Descendants(Total_Co<br>stCenter)<br>Years - from airflow variable<br>Scenario - from airflow<br>variable<br>Version - from airflow variable<br>Period - BegBalance,<br><period> passed from airflow<br>variables<br>View -<br>VTR_PLAN - Periodic<br>Day -<br>VTR_PLAN - No_Day<br>TimingCard -<br>VTR_PLAN -<br>ILvl0Descendants(Current_<br>TimingCard)||||||
|---|---|---|---|---|---|---|---|
|||Updated PlanElement for<br>FIN_PLAN -<br>Actuals -<br>ILvl0Descendants(Actuals_De<br>tail),Actuals_Allocations<br>Forecast & Plan -<br>ILvl0Descendants(Total_Plan)<br>,CorpFPA_Adjustment<br>We will fetch ILvl0Descendants<br>of Actuals_Detail and Total_Plan,<br>so the plan element columnin<br>EGDL will show all the<br>respective plan elements.We<br>will let the consumers look at<br>the data and then we can|@M|@Ryan<br>Ward<br>@Abhis||||
||||anoj|||||
|||||||||
||||Gan|||||
||||l|||||
||||gu|hek||||
||||a|Marathe<br>@Piyoo<br>sh Pant<br>@Protim||||



|||consolidate everything to a<br>single plan element like<br>Total_Plan based on the<br>feedback.<br>When we fetch<br>ILvl0Descendants(Actuals_Detai<br>l),all the plan elements under<br>this parentincluding the negates<br>will be retrieved.Users should<br>be able to filter these by<br>selecting the plan element they<br>need.We can update these<br>based on the users feedback<br>and use cases.|||||
|---|---|---|---|---|---|---|
|||OKC - Loyality accounts (<br>)<br>These new accounts are setupin<br>Hyperion to support OKC<br>Dashboard and need to be part of<br>the data thatis being published to<br>EGDL.<br>@ManojGangula<br>@Abhishek Marathe<br>Loyalty Pgrm Earn - PDRP<br>Loyalty Cost (SR0708)<br>Loyalty Pgrm Earn - PDRP<br>Claims Cost (SR0709)<br>Loyalty Pgrm Earn - OK Earn<br>Initiatives (SR0710)<br>Loyalty Pgrm Cost - Targeted<br>CRM (SR0711)<br>[FSIT-<br>166797] Create new stat accounts<br>for Loyalty Data - Expedia Jira|||||
||||||||



