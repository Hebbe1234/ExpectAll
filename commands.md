## Table 1
The results in `EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1_PRECOMP` are the extrapolated data from based on `EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1`. The extrapolation is done using `compute_pre_compute_time.py`

Go to the folder `src/mkplot` and run the following command
```bash
python make_table.py
```
## Figure 3
Go to the folder `drawBoxPLot` and run the following commands
```bash
python ExtractMipData.py
python ExtractBDDData.py
python 3boxPlot369.py

```
Plots are output to the folders:
Single369dt_all_times and Single369kanto_all_times


## Figure 4
Go to the folder `drawBoxPLot` and run the following commands
```bash
python ExtractMipData.py
python ExtractBDDData.py
python 1ILPAndBdd.py

```
Plots are output to the folders:
ILPvsBDD_all_times_dt and ILPvsBDD_all_times_kanto

## Figure 5
Go to the folder `drawBoxPLot` and run the following commands
```bash
python ExtractMipData.py
python ExtractBDDData.py
python 2nonChaningILPAndBDD.py 

```
Plots are output to the folders:
ILPvsBDD_no_change_query_times_dt and  ILPvsBDD_no_change_query_times_kanto

## Table 3 and 4
Go to the folder `drawBoxPLot` and run the following commands
```bash
python ExtractForTableFailover.py
python GenerateCsvForFailoverTables.py
```

## Figure 6
The results in `EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1_PRECOMP` are the extrapolated data from based on `EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1`. The extrapolation is done using `compute_pre_compute_time.py`

```bash
python fancy_scatter_failover.py --data_dir ../../out/Reproduceability/EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1_PRECOMP/results ../../out/Reproduceability/EXPERIMENT_FAILOVER_BUILD_QUERY_RUN_D1_9/results --save_dir=Reproduceability/Figure_6/ --plot_rows=topology --plot_cols=fake_col --line_values demands experiment --x_axis par5 --aggregate=file --y_axis failover_plus_build_time --change_values_file topology  --config ./fancy_scatter_plots/Reproduceability/Figure_6/config.json  ./fancy_scatter_plots/Reproduceability/Figure_6/config_failures_bdd.json --max_y -1
```



## Figure 7a
```bash
python3 fancy_cactus.py --y_axis max_demands --solved_only yes --line_values experiment --change_values_file seed --filter_experiments topozoo_best_clique gap_free_safe_limited_super_safe topozoo_best_subspectrum --data_dir ../../out/Reproduceability/Epilogue/EXPERIMENT_TOPOLOGY_ZOO_SUB_SPECTRUM_RUN_4/results ../../out/Reproduceability/Epilogue/EXPERIMENT_TOPOLOGY_ZOO_CLIQUE_RUN_8/results ../../out/Reproduceability/Epilogue/EXPERIMENT_RSA_IMPROVED_RUN_1/results  --save_dir Reproduceability/epilogue/ --config ./fancy_scatter_plots/Reproduceability/epilogue/config.json --x_axis instance
```

## Figure 7b
```bash

python3 fancy_cactus.py --y_axis usage --solved_only yes --line_values experiment --change_values_file demands --filter_experiments topozoo_best_clique gap_free_safe_limited_super_safe topozoo_best_subspectrum --data_dir ../../out/Reproduceability/Epilogue/EXPERIMENT_TOPOLOGY_ZOO_SUB_SPECTRUM_RUN_4/results ../../out/Reproduceability/Epilogue/EXPERIMENT_TOPOLOGY_ZOO_CLIQUE_RUN_8/results ../../out/Reproduceability/Epilogue/EXPERIMENT_RSA_IMPROVED_RUN_1/results  --save_dir Reproduceability/epilogue/ --config ./fancy_scatter_plots/Reproduceability/epilogue/config_usage.json --x_axis instance


```


## Figure 7c
```bash

python3 fancy_cactus.py --y_axis k_link_resillience --solved_only yes --line_values experiment --change_values_file demands --data_dir ../../out/Reproduceability/Epilogue/EXPERIMENT_CLIQUE_RESIL_RUN_1/results --save_dir Reproduceability/epilogue/ --config ./fancy_scatter_plots/Reproduceability/epilogue/config_edge_eval.json --x_axis instance


```

