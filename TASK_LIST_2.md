# TASK_LIST: Adjustments to Make

## 1. Modularize: Streamline Notebooks and scripts

Currently each notebook uses a verbose amount of not-very-'DRY' code to run calculations that should already be streamlined by the script files.

This project, 'gri', should really be thought of more as a share-able module to make it easy for anyone to calculate "GRI" metrics for their survey data.
It should be easy to configure (hence config files ...) and provide a robust, clear, streamlined functions/ import modules to very easily calculate GRI.

With the provided config files, benchmark data, and survey data, we should be able to produce Notebooks that demonstrate *how cleanly* and with *how few lines of code* one can use to calculate GRI scores and run more advanced analysis. Add this high-level goal (creating a streamlined, easy-to-use and and clean, efficient code to run GRI calculations, GRI module more than a collection of bespoke scripts/notebooks. The notebooks should be demonstrating how clean it is to use this GRI module and import the specific modules/functions neeeded to calculate GRI.

Review each of the notebooks and take notes on where you see opportunities for streamlining, cleanup, simplifying, and better following of reasonable DRY principles.

Then, review the script files and add to this document where you see how the scripts can be streamlined and offer better module-like behavior, keeping in mind how users (like in the notebooks) would actually use a GRI module to calculate metrics on survey data.

Finally, review the notes  in this document and come up with a detailed plan for how we will "modularize" GRI and update the Notebooks to demonstrate the power of the GRI module rather than repeating bespoke, custom code.

## 2. Better integrate @calculate_max_possible_scores.py into the module.

Should be able to calcuate GRI scores of a survey and *also* get the "Max possible" of that metric as well for the sample size of the total survey sample size. For easy comparison, let's also add an output showing the "% of max possible for given sample size" for each Score metric (GRI, Diversity score) as well.

This should be demonstrated in a notebook and also when one runs `make calculate-gri`. Again, this should work as a module with easy-to-call functions and NOT repeating similar code in multiple places.

## 3. Add WVS survey data to @6-survey-comparison.ipynb

Add a comparison of both WVS survey datasets scores compared to GD.

## 4. Flesh out remainder of @2-gri-calculation-example.ipynb

This notebook seems to awkwardly end right at "## 2. Top Contributing Segments Analysis" without clearly giving analysis. Appropriately wrap up this notebook and implement anything missing in this analysis, again keeping in mind the updated Module-oriented approach.

