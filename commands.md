# Fig 4 & 8
```bash
cd ..
python .\reordering_analysis.py
```

# Fig 5a
```bash
python convert_to_csv.py -dir ../../out/bdd_baseline_wavelengths_effect_run33/ -x 6 -savedest csv/wavelengths.csv -yfill 3600

python3 AAU_scatter.py -d csv/wavelengths.csv -xlabel Wavelengths -ylabel "Run time (s)" -agg 0 -x 6 -savedest new_graphs/median_wavelengths -agg_func median
```


# Fig 5b
```bash
python3 convert_to_csv.py -dir ../../out/bdd_baseline_wavelengths_effect_run33/ -x 6 -savedest csv/wavelengths_nopad.csv

python3 AAU_barchart.py -d csv/wavelengths_nopad.csv -xlabel Wavelengths -ylabel "Problems timed out" -agg 7 -x 6 -savedest new_graphs/bar_wavelengths

```


# Fig 6a
```bash
python3 convert_to_csv.py -dir ../../out/bdd_baseline_run_demands_some_68/ -x 5 -savedest csv/demands.csv -yfill 3600

python3 AAU_scatter.py -d csv/demands.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/median_demands -agg_func median
```


# Fig 6b
```bash
python3 convert_to_csv.py -dir ../../out/bdd_baseline_run_demands_some_68/ -x 5 -savedest csv/demands_nopad.csv

python3 AAU_barchart.py -d csv/demands_nopad.csv -xlabel Demands -ylabel "Problems timed out" -agg 7 -x 5 -savedest new_graphs/bar_demands

```

# Fig 7
```bash
python AAU_create_json_and_make_pdfs.py --legend baseline MIP --xaxis 1 2 --dirs bdd_baseline_run mip_source_aggregation_1  --savedest cactus_graphs/baseline_mip_compare   
```

# Fig 10
```bash
python AAU_create_json_and_make_pdfs.py --legend baseline rwa-inc-par rwa-inc --xaxis 1 0 1  --dirs bdd_baseline_run bdd_increasing_parallel_run1 bdd_increasing_run  --savedest cactus_graphs/baseline_increasing
```

# Fig 11
```bash
python AAU_create_json_and_make_pdfs.py --legend baseline rwa-seq rwa-lim  --xaxis 1 1 1 --dirs bdd_baseline_run sequence_run bdd_wavelength_constraint_run  --savedest cactus_graphs/baseline_equivalence_        
```

# Fig 12
```bash 
python AAU_create_json_and_make_pdfs.py --legend baseline rwa-conq-par  --xaxis 1 1 --dirs bdd_baseline_run dynamic_add_parallel1 --savedest cactus_graphs/baseline_dynamic_par_     
```

# Fig 13
```bash
python AAU_create_json_and_make_pdfs.py --legend baseline add-last add-full  --xaxis 1 0 1 --dirs bdd_baseline_run dynamic_add_last_all_run2 dynamic_add_last_all_run2_cp --savedest cactus_graphs/add_last
```

# Fig 14
```bash
python AAU_create_json_and_make_pdfs.py --legend baseline "rwa-inc-par" "rwa-seq" "rwa-conq-par" "rwa-inc-par-seq" "rwa-conq-inc-par-lim" --xaxis 1 0 1 0 0 0  --dirs bdd_baseline_run  bdd_increasing_parallel_run1 sequence_run dynamic_add_parallel1 bdd_increasing_parallel_sequential_run1  bdd_increasing_parallel_dynamic_limited_run_demands_all1 --savedest cactus_graphs/compare_a_lot
```

# Fig 15
```bash
python AAU_create_json_and_make_pdfs.py --legend baseline MIP "rwa-inc-par-seq" --xaxis 1 2 0 --dirs bdd_baseline_run mip_source_aggregation_1 bdd_increasing_parallel_sequential_run1 --savedest cactus_graphs/compare_with_mip  
```